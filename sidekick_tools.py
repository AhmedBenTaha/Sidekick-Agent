
"""Tools for the Sidekick: search, notifications, memory, tasks, documents, and MCP."""

import asyncio
import os
from contextlib import AsyncExitStack
from pathlib import Path

import aiosqlite
import requests
import wikipedia
from dotenv import load_dotenv
from docx import Document
from pypdf import PdfReader

from langchain_community.tools import GoogleSerperRun, WikipediaQueryRun
from langchain_community.utilities import (
    GoogleSerperAPIWrapper,
    WikipediaAPIWrapper,
)
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools


load_dotenv(override=True)

# Configuration
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = BASE_DIR / "documents"
DB_PATH = DATA_DIR / "sidekick.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

wikipedia.set_user_agent(
    "Sidekick-Agent/1.0 (ahmedbinaltaha@gmail.com)"
)

search_tool = GoogleSerperRun(
    api_wrapper=GoogleSerperAPIWrapper()
)

wikipedia_tool = WikipediaQueryRun(
    api_wrapper=WikipediaAPIWrapper()
)


# Database initialization
async def init_db():
    """Initialize local memory and task tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.commit()


# Notifications
@tool
def send_push_notification(text: str) -> str:
    """Send a short push notification to the user's phone."""
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")

    if not token or not user:
        return "Missing PUSHOVER_TOKEN or PUSHOVER_USER in .env."

    try:
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": token,
                "user": user,
                "message": text[:1024],
            },
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("status") != 1:
            return "Pushover did not confirm the notification."

        return "Notification sent."

    except requests.RequestException:
        return "Failed to send notification due to a network or API error."


# Human assistance
@tool
def request_human_help(instructions: str) -> str:
    """Tell the user what manual action is needed.

    This tool does not itself pause execution or verify user approval.
    """
    return (
        "Human assistance required. Ask the user to complete this step: "
        + instructions
    )


# Persistent memory
@tool
async def save_memory(content: str) -> str:
    """Save a user-approved fact or preference for future sessions."""
    content = content.strip()

    if not content:
        return "Memory cannot be empty."

    if len(content) > 5000:
        return "Memory is too long. Limit it to 5000 characters."

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO memories (content) VALUES (?)",
            (content,),
        )
        await db.commit()

    return "Memory saved."


@tool
async def search_memories(query: str) -> str:
    """Search saved memories using keyword matching."""
    query = query.strip()

    if not query:
        return "Please provide a search query."

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, content, created_at
            FROM memories
            WHERE content LIKE ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (f"%{query}%",),
        )
        rows = await cursor.fetchall()

    if not rows:
        return "No matching memories found."

    return "\n".join(
        f"Memory {row[0]} ({row[2]}): {row[1]}"
        for row in rows
    )


# Task manager

@tool
async def add_task(title: str) -> str:
    """Add a task to the user's local task list."""
    title = title.strip()

    if not title:
        return "Task title cannot be empty."

    if len(title) > 500:
        return "Task title is too long."

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tasks (title) VALUES (?)",
            (title,),
        )
        task_id = cursor.lastrowid
        await db.commit()

    return f"Task added with ID {task_id}."


@tool
async def list_tasks(show_completed: bool = False) -> str:
    """List pending tasks, or all tasks if show_completed is true."""
    async with aiosqlite.connect(DB_PATH) as db:
        if show_completed:
            cursor = await db.execute(
                """
                SELECT id, title, done, created_at
                FROM tasks
                ORDER BY id DESC
                LIMIT 100
                """
            )
        else:
            cursor = await db.execute(
                """
                SELECT id, title, done, created_at
                FROM tasks
                WHERE done = 0
                ORDER BY id DESC
                LIMIT 100
                """
            )

        rows = await cursor.fetchall()

    if not rows:
        return "No tasks found."

    return "\n".join(
        f"[{'x' if row[2] else ' '}] Task {row[0]}: {row[1]}"
        for row in rows
    )


@tool
async def complete_task(task_id: int) -> str:
    """Mark an existing task as completed."""
    if task_id <= 0:
        return "Task ID must be a positive integer."

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE tasks SET done = 1 WHERE id = ?",
            (task_id,),
        )
        await db.commit()
        updated = cursor.rowcount

    if not updated:
        return f"Task {task_id} was not found."

    return f"Task {task_id} marked as completed."


# Document reader
@tool
def read_document(file_path: str) -> str:
    """Read a PDF or DOCX file located inside the documents folder.

    Provide a relative path, such as report.pdf.
    """
    try:
        base = DOCUMENTS_DIR.resolve()
        target = (base / file_path).resolve()

        # Prevent path traversal outside the allowed directory.
        if not target.is_relative_to(base):
            return "Access denied: path is outside the documents folder."

        if not target.is_file():
            return "File not found."

        suffix = target.suffix.lower()

        if suffix == ".pdf":
            reader = PdfReader(str(target))

            extracted = []
            for page in reader.pages[:30]:
                extracted.append(page.extract_text() or "")

            content = "\n".join(extracted)

        elif suffix == ".docx":
            doc = Document(str(target))
            content = "\n".join(
                paragraph.text for paragraph in doc.paragraphs
            )

        else:
            return "Unsupported file type. Use PDF or DOCX."

        if not content.strip():
            return "No extractable text found in the document."

        return content[:15000]

    except Exception:
        return "Could not read the document. Check that it is valid and accessible."


# MCP connections
def mcp_connections(sandbox: str) -> dict:
    """Configure the Playwright and filesystem MCP servers."""
    return {
        "playwright": {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "@playwright/mcp@latest",
                "--isolated",
            ],
        },
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                str(Path(sandbox).resolve()),
            ],
        },
    }


# Persistent MCP sessions
class McpSessions:
    """Keep MCP sessions alive until stop() is called."""

    def __init__(self, connections: dict):
        self.connections = connections
        self.tools = []
        self._ready = asyncio.Event()
        self._stop = asyncio.Event()
        self._task = None

    async def _run(self):
        client = MultiServerMCPClient(self.connections)

        async with AsyncExitStack() as stack:
            for name in self.connections:
                session = await stack.enter_async_context(
                    client.session(name)
                )

                self.tools += await load_mcp_tools(
                    session,
                    server_name=name,
                )

            self._ready.set()
            await self._stop.wait()

    async def start(self) -> list:
        self._task = asyncio.create_task(self._run())
        ready = asyncio.create_task(self._ready.wait())

        try:
            await asyncio.wait(
                [ready, self._task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if self._task.done():
                self._task.result()

            return self.tools

        finally:
            if not ready.done():
                ready.cancel()

    def stop(self):
        """Request graceful shutdown of the MCP sessions."""
        self._stop.set()

    async def wait_closed(self):
        """Wait for the session task to finish and resources to close."""
        if self._task is not None:
            await self._task


# Collect all tools
async def get_all_tools(sandbox: str):
    """Return all local and MCP tools plus the session manager."""
    await init_db()

    sessions = McpSessions(mcp_connections(sandbox))
    mcp_tools = await sessions.start()

    our_tools = [
        search_tool,
        wikipedia_tool,
        send_push_notification,
        request_human_help,
        save_memory,
        search_memories,
        add_task,
        list_tasks,
        complete_task,
        read_document,
    ]

    return our_tools + mcp_tools, sessions
