"""Gradio app for the Sidekick. Run with: uv run app.py"""

import asyncio
import html

import gradio as gr

import styles
from sidekick import Sidekick


# ==========================================
# LAUNCH CONFIGURATION
# ==========================================

LAUNCH_STYLE = {
    "theme": styles.THEME,
    "css": styles.CSS,
    "head": styles.JS,
}


# ==========================================
# UI COMPONENTS & HTML
# ==========================================

HEADER = """
<div id="header">
    <div class="context-label">Your personal co-worker</div>
    <h1>Sidekick</h1>
    <div class="brand-bar"></div>
</div>
"""


def render_todos(todos):
    """Render the execution plan panel with polished, semantic HTML."""
    if not todos:
        items = (
            '<div class="placeholder">'
            "The Sidekick will write its plan here as it works."
            "</div>"
        )
    else:
        items = "<ul>" + "".join(
            f'<li class="{html.escape(str(todo.get("status", "pending")), quote=True)}">'
            f'<span class="mark"></span>'
            f'<span class="text">{html.escape(str(todo.get("content", "")))}</span>'
            "</li>"
            for todo in todos
        ) + "</ul>"

    return f"<h3>Execution Plan</h3>{items}"


# ==========================================
# EVENT HANDLERS
# ==========================================

async def setup():
    """Initialize the Sidekick agent and enable the UI."""
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick, gr.update(interactive=True)


async def process_message(
    sidekick, message, success_criteria, history
):
    """Process a user message and return the updated chat history."""
    if sidekick is None:
        return history, gr.update(visible=False), sidekick

    if not message or not message.strip():
        return history, gr.update(visible=False), sidekick

    results = await sidekick.run_turn(
        message.strip(),
        success_criteria,
        history,
    )

    return (
        results,
        gr.update(visible=sidekick.paused),
        sidekick,
    )


async def approve(sidekick, history):
    """Approve the current step and resume the agent."""
    if sidekick is None or not sidekick.paused:
        return history, gr.update(visible=False), sidekick

    results = await sidekick.resume(history)

    return (
        results,
        gr.update(visible=sidekick.paused),
        sidekick,
    )


def watch_todos(sidekick):
    """Refresh the plan panel without locking it during agent execution."""
    return render_todos(sidekick.todos) if sidekick else render_todos([])


async def reset(sidekick):
    """Reset the application state and initialize a fresh Sidekick."""
    if sidekick:
        await sidekick.cleanup()

    new_sidekick = Sidekick()
    await new_sidekick.setup()

    return (
        "",
        "",
        None,
        gr.update(visible=False),
        new_sidekick,
    )


def free_resources(sidekick):
    """Schedule asynchronous cleanup when Gradio deletes the state."""
    if sidekick is None:
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(sidekick.cleanup())
    else:
        loop.create_task(sidekick.cleanup())


# ==========================================
# UI LAYOUT
# ==========================================

with gr.Blocks(title="Sidekick", fill_width=True) as ui:
    gr.HTML(HEADER)

    sidekick_state = gr.State(delete_callback=free_resources)

    # Main Content Area: Chat and Plan Panel
    with gr.Row(equal_height=True):
        chatbot = gr.Chatbot(
                label="Conversation",
                height=520,
                scale=3,
                elem_id="chat",
                buttons=["copy"],
                placeholder=(
                    "<div style='text-align: center; padding: 40px; color: #94A3B8;'>"
                    "<h3 style='color: #0F172A; margin-bottom: 8px; font-family: Inter, sans-serif;'>"
                    "Ready to assist</h3>"
                    "<p style='font-family: Inter, sans-serif;'>"
                    "Type your request below to get started."
                    "</p>"
                    "</div>"
                ),
            )

        with gr.Column(scale=1, min_width=300):
            todos_panel = gr.HTML(
                render_todos([]),
                elem_id="plan-panel",
            )

    # Command Center Input Area
    with gr.Column(elem_id="ask-panel"):
        with gr.Row(equal_height=True):
            message = gr.Textbox(
                show_label=False,
                placeholder="What would you like to achieve?",
                lines=1,
                scale=3,
                autofocus=True,
            )
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="How will we know it's done? (Optional)",
                lines=1,
                scale=2,
            )

    # Action Buttons
    with gr.Row():
        reset_button = gr.Button(
            "Reset",
            elem_id="reset-button",
            size="sm",
        )
        
        approve_button = gr.Button(
            "Approve & Continue",
            visible=False,
            elem_id="approve-button",
            size="lg",
        )

        go_button = gr.Button(
            "Execute",
            elem_id="go-button",
            interactive=False,
            size="lg",
            variant="primary",
        )

    # Background Timer for Plan Updates
    timer = gr.Timer(1)

    # ==========================================
    # EVENT BINDINGS
    # ==========================================

    ui.load(
        setup,
        inputs=[],
        outputs=[sidekick_state, go_button],
    )

    timer.tick(
        watch_todos,
        inputs=[sidekick_state],
        outputs=[todos_panel],
        show_progress="hidden",
    )

    # Bind all input triggers to the same processing function
    input_triggers = [message.submit, success_criteria.submit, go_button.click]
    for trigger in input_triggers:
        trigger(
            process_message,
            inputs=[
                sidekick_state,
                message,
                success_criteria,
                chatbot,
            ],
            outputs=[chatbot, approve_button, sidekick_state],
        )

    approve_button.click(
        approve,
        inputs=[sidekick_state, chatbot],
        outputs=[chatbot, approve_button, sidekick_state],
    )

    reset_button.click(
        reset,
        inputs=[sidekick_state],
        outputs=[
            message,
            success_criteria,
            chatbot,
            approve_button,
            sidekick_state,
        ],
    )


if __name__ == "__main__":
    ui.launch(
        inbrowser=True,
        **LAUNCH_STYLE,
    )