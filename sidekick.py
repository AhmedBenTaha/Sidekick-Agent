"""Sidekick: a create_agent worker wrapped in an evaluator/retry loop."""

import os
import uuid
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentMiddleware,
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
    PIIMiddleware,
    TodoListMiddleware,
)
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from sidekick_tools import get_all_tools

load_dotenv(override=True)

HERE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(HERE, "sandbox")
MAX_ATTEMPTS = 3


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Brief, concrete feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the stated success criteria were met")
    user_input_needed: bool = Field(
        description="True if clarification or another user action is genuinely needed"
    )


WORKER_PROMPT = """You are Sidekick, a capable personal assistant who completes tasks for the user.
You have web search, Wikipedia, a browser, a sandbox filesystem, local task/memory tools, a document reader,
and the ability to send push notifications.
When using the browser, navigate to a page and inspect its snapshot rather than clicking around unnecessarily.
Handle dismissible cookie banners when appropriate. Never claim you logged in, passed a CAPTCHA, completed
2FA, or finished a manual action unless the tool results or the user confirm it.
If a task requires a human-only step, use request_human_help to explain exactly what the user must do, then ask
for confirmation before assuming it is complete. That tool itself does not pause execution or verify completion.
For flight searches, you may open Google Flights and search using the user's route and dates.
Keep working until the success criteria are met, or until you genuinely need clarification. In your final answer,
state what you did, what you produced, and what you found. Be truthful about tool failures and uncertainty."""


class TolerateToolErrors(AgentMiddleware):
    """Return tool failures to the model so it can attempt recovery."""

    async def awrap_tool_call(self, request, handler):
        try:
            return await handler(request)
        except Exception as error:
            return ToolMessage(
                content=f"That tool call failed ({type(error).__name__}): {error}. Try another approach.",
                tool_call_id=request.tool_call["id"],
            )


class Sidekick:
    def __init__(self):
        self.sidekick_id = str(uuid.uuid4())
        self.memory = InMemorySaver()
        self.tools = None
        self.sessions = None
        self.worker = None
        self.evaluator = None
        self.task = ""
        self.success_criteria = ""
        self.attempts = 0
        self.paused = False
        self.pending_actions = 0
        self.todos = []
        self._turn_message_start = 0

    async def setup(self):
        """Initialize tools/MCP sessions and construct the worker and evaluator."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENROUTER_API_KEY in .env.")

        os.makedirs(SANDBOX, exist_ok=True)
        self.tools, self.sessions = await get_all_tools(SANDBOX)
        try:
            model_kwargs = {
                "model": "dots-studio/dots-3-note-preview:free",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": api_key,
                "temperature": 0,
            }
            worker_model = ChatOpenAI(**model_kwargs)
            evaluator_model = ChatOpenAI(**model_kwargs)

            self.worker = create_agent(
                model=worker_model,
                tools=self.tools,
                system_prompt=(
                    f"{WORKER_PROMPT}\nToday is {datetime.now():%A %d %B %Y}."
                ),
                middleware=[
                    TolerateToolErrors(),
                    TodoListMiddleware(),
                    PIIMiddleware("email"),
                    PIIMiddleware("credit_card", apply_to_tool_results=True),
                    ModelCallLimitMiddleware(run_limit=30),
                    # Notifications are an external side effect. Human-help is not
                    # gated here because it only communicates instructions to the user.
                    HumanInTheLoopMiddleware(
                        interrupt_on={"send_push_notification": True}
                    ),
                ],
                checkpointer=self.memory,
            )
            # Function-calling structured output is generally more compatible with
            # OpenRouter providers than requiring native JSON-schema output.
            self.evaluator = evaluator_model.with_structured_output(
                EvaluatorOutput, method="function_calling"
            )
        except Exception:
            await self.cleanup()
            raise

    async def evaluate(
        self, message: str, success_criteria: str, last_reply: str, tools_used: list[str]
    ) -> EvaluatorOutput:
        prompt = f"""You evaluate whether an assistant has met the user's success criteria.

User request:
{message}

Success criteria:
{success_criteria}

Tools called during this task (names only; a call is not proof it succeeded):
{", ".join(tools_used) or "none"}

Assistant's most recent final reply:
{last_reply}

Judge conservatively. Do not assume a tool succeeded merely because it was called. If the reply
admits that required information/action is missing, the criteria are not met. Set user_input_needed
only when a user answer/action is genuinely required; do not use it just because work is incomplete.
Give brief, concrete feedback identifying any unmet criterion."""
        return await self.evaluator.ainvoke(prompt)

    async def _get_message_count(self, config: dict) -> int:
        """Get the checkpoint's existing message count, if a state already exists."""
        try:
            snapshot = await self.worker.aget_state(config)
            values = getattr(snapshot, "values", {}) or {}
            return len(values.get("messages", []))
        except Exception:
            return 0

    async def run_turn(self, message: str, success_criteria: str, history: list) -> list:
        """Start a new task and retry it with evaluator feedback up to MAX_ATTEMPTS."""
        if self.worker is None or self.evaluator is None:
            raise RuntimeError("Call await sidekick.setup() before run_turn().")

        self.task = message
        self.success_criteria = success_criteria.strip() or "The answer should be clear, correct and complete."
        self.attempts = 0
        self.todos = []
        self.paused = False
        self.pending_actions = 0

        config = {"configurable": {"thread_id": self.sidekick_id}}
        self._turn_message_start = await self._get_message_count(config)
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"{message}\n\nSuccess criteria for this task: "
                        f"{self.success_criteria}"
                    ),
                }
            ]
        }
        return await self._advance(
            payload, history + [{"role": "user", "content": message}]
        )

    async def resume(self, history: list) -> list:
        """Approve all actions currently paused for human review and resume the same turn."""
        if not self.paused or self.pending_actions < 1:
            return history + [{"role": "assistant", "content": "There are no pending actions to approve."}]

        payload = Command(
            resume={
                "decisions": [{"type": "approve"} for _ in range(self.pending_actions)]
            }
        )
        self.paused = False
        self.pending_actions = 0
        return await self._advance(payload, history)

    @staticmethod
    def _content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(content)

    def _extract_reply_and_tools(self, result: dict) -> tuple[str, list[str]]:
        messages = result.get("messages", []) or []
        current_turn_messages = messages[self._turn_message_start :]
        tools_used = [
            call.get("name", "unknown_tool")
            for msg in current_turn_messages
            for call in (getattr(msg, "tool_calls", None) or [])
        ]
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and not (getattr(msg, "tool_calls", None) or []):
                return self._content_to_text(msg.content), tools_used
        if messages:
            return self._content_to_text(getattr(messages[-1], "content", "")), tools_used
        return "The agent finished without returning any messages.", tools_used

    @staticmethod
    def _interrupt_actions(result: dict) -> list:
        interrupts = result.get("__interrupt__") or []
        if not interrupts:
            return []
        value = getattr(interrupts[0], "value", {}) or {}
        if isinstance(value, dict):
            return value.get("action_requests", []) or []
        return []

    async def _advance(self, payload, history: list) -> list:
        config = {"configurable": {"thread_id": self.sidekick_id}}
        while True:
            result = None
            async for state in self.worker.astream(
                payload, config=config, stream_mode="values"
            ):
                result = state
                self.todos = state.get("todos", self.todos)

            if not isinstance(result, dict):
                return history + [
                    {"role": "assistant", "content": "The agent stopped without returning a usable state."}
                ]

            actions = self._interrupt_actions(result)
            if actions:
                self.paused = True
                self.pending_actions = len(actions)
                descriptions = []
                for action in actions:
                    description = action.get("description") or action.get("name") or "Action requires approval"
                    args = action.get("args")
                    if args:
                        description = f"{description}\nArguments: {args}"
                    descriptions.append(str(description))
                return history + [
                    {
                        "role": "assistant",
                        "content": "Waiting for your approval before proceeding:\n\n"
                        + "\n\n".join(descriptions),
                    }
                ]

            self.paused = False
            self.pending_actions = 0
            reply, tools_used = self._extract_reply_and_tools(result)
            self.attempts += 1
            verdict = await self.evaluate(
                self.task, self.success_criteria, reply, tools_used
            )

            if (
                verdict.success_criteria_met
                or verdict.user_input_needed
                or self.attempts >= MAX_ATTEMPTS
            ):
                return history + [
                    {"role": "assistant", "content": reply},
                    {"role": "assistant", "content": f"Evaluator: {verdict.feedback}"},
                ]

            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Your last response did not meet the success criteria. "
                            f"Evaluator feedback: {verdict.feedback} Please continue working "
                            "on the original task and address this feedback."
                        ),
                    }
                ]
            }

    async def cleanup(self) -> None:
        """Gracefully stop MCP servers and close their sessions."""
        sessions = self.sessions
        self.sessions = None
        if sessions is not None:
            sessions.stop()
            try:
                await sessions.wait_closed()
            except Exception:
                # Preserve the original exception if cleanup follows a failed setup.
                pass
