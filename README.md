::: {align="center"}
# ⚡ Sidekick

### Your personal AI co-worker --- built to plan, act, and ask when it matters.

A tool-using AI assistant with an evaluator loop, live task planning,
MCP integrations, and human approval for selected actions.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Gradio](https://img.shields.io/badge/UI-Gradio-FF7C00?style=for-the-badge&logo=gradio&logoColor=white)
![MCP](https://img.shields.io/badge/Integrations-MCP-753991?style=for-the-badge)
![LLM](https://img.shields.io/badge/LLM-OpenRouter-032147?style=for-the-badge)

**Not just a chatbot. A workflow-oriented assistant that can use tools,
check its work, and pause for human input.**
:::

------------------------------------------------------------------------

## ✨ What is Sidekick?

Sidekick is an experimental AI co-worker built around an agent loop: it
receives a task, uses tools to make progress, evaluates the result
against success criteria, and can retry when the result needs
improvement.

The interface is designed to make that process visible. You can watch
the task plan update, provide success criteria, and approve selected
actions that need a human in the loop.

> **Project status:** This is a development project. Test the code and
> integrations with your installed dependency versions and API
> credentials before relying on them for real workflows.

## 🚀 Highlights

-   **Agent + evaluator loop** --- a worker handles the task while an
    evaluator checks whether the stated success criteria were met.
-   **Bounded retries** --- the agent can revise its attempt using
    evaluator feedback, with a configured maximum number of attempts.
-   **Live task plan** --- a Gradio timer refreshes the plan panel while
    the agent works.
-   **MCP integrations** --- connect to Playwright and a filesystem
    server through the Model Context Protocol.
-   **Local tools** --- Serper web search, Wikipedia lookup, document
    reading, SQLite-backed memories and tasks, push notifications, and a
    human-help request tool.
-   **Human-in-the-loop checkpoint** --- selected actions, such as
    sending a push notification, can pause for approval before
    continuing.
-   **Guardrails and limits** --- middleware is configured for
    tool-error handling, PII detection on selected tool results, and a
    model-call limit.
-   **Branded UI** --- light mode, navy and blue foundations, with gold
    for approval moments and purple as a secondary accent.

## 🧭 How it works

``` mermaid
flowchart TD
    A[User request + success criteria] --> B[Sidekick worker agent]
    B --> C[Tools and MCP servers]
    C --> D[Worker response]
    D --> E[Evaluator]
    E -->|Criteria met| F[Return result]
    E -->|Needs improvement| G[Feedback and retry]
    G --> B
    B --> H[Approval checkpoint]
    H -->|Approved| C
    H -->|Needs human input| I[User interaction]
```

The exact path depends on the request and the tools selected by the
agent. Not every task needs every component.

## 🖥️ Interface

-   A chat panel for requests and responses.
-   A live **Plan** panel showing pending, in-progress, and completed
    tasks.
-   A field for optional success criteria.
-   **Go!** to start work.
-   **Approve and continue** when an approval checkpoint is waiting.
-   **Reset** to start a fresh agent session.

## 🧰 Tools and integrations

  -----------------------------------------------------------------------
  Capability                          What it is for
  ----------------------------------- -----------------------------------
  Serper search                       Search the web using a configured
                                      Serper API key

  Wikipedia                           Retrieve reference information

  Playwright MCP                      Browser automation through the
                                      configured Playwright MCP server

  Filesystem MCP                      File operations scoped to the
                                      configured sandbox directory

  Document reader                     Read supported PDF and DOCX files
                                      from the documents directory

  SQLite memory                       Save and search simple text
                                      memories

  SQLite tasks                        Add, list, and complete tasks

  Pushover                            Send a push notification when
                                      configured

  Human-help tool                     Ask the user to perform or verify a
                                      step requiring human involvement
  -----------------------------------------------------------------------

**Important boundaries:** The human-help tool cannot verify that a
person completed an instruction. The document reader does not perform
OCR. PII middleware does not guarantee that sensitive information is
filtered from every possible path. Human approval is configured for
selected actions, not every browser or filesystem operation.

## 🏗️ Project structure

``` text
.
├── app.py              # Gradio interface and event handlers
├── sidekick.py         # Agent, evaluator loop, middleware, and approvals
├── sidekick_tools.py   # Local tools and MCP session management
├── styles.py           # Theme, CSS, and JavaScript
├── documents/          # Documents available to the document-reading tool
└── ...                 # Project configuration and dependency files
```

The exact files and directories may vary depending on your local setup.

## ⚙️ Getting started

### 1. Requirements

-   Python 3.11 or a compatible version supported by your dependencies.
-   [uv](https://docs.astral.sh/uv/) for running the project and
    managing dependencies.
-   Node.js and `npx` for launching the configured MCP servers.
-   API credentials for the services you intend to use.

### 2. Install dependencies

If the project already has a `pyproject.toml`, install dependencies
with:

``` bash
uv sync
```

For a manual setup, the core packages used by the app include:

``` bash
uv add gradio langchain langchain-openai langchain-community langgraph \
  langchain-mcp-adapters python-dotenv aiosqlite requests wikipedia \
  python-docx pypdf
```

Choose compatible versions for your code. Gradio, LangChain, and MCP
adapter APIs can change between releases.

### 3. Configure environment variables

Create a `.env` file in the project root:

``` dotenv
OPENROUTER_API_KEY=your_openrouter_api_key
SERPER_API_KEY=your_serper_api_key
PUSHOVER_TOKEN=your_pushover_app_token
PUSHOVER_USER=your_pushover_user_key
```

-   `OPENROUTER_API_KEY` is needed for the configured language models.
-   `SERPER_API_KEY` enables Serper web search.
-   `PUSHOVER_TOKEN` and `PUSHOVER_USER` are needed for Pushover
    notifications.

Only configure credentials for services you plan to use. Never commit
`.env` or real API keys to GitHub.

### 4. Check MCP prerequisites

The app launches MCP servers using `npx`. Check that Node.js and npm/npx
are available:

``` bash
node --version
npm --version
npx --version
```

Review the configured Playwright and filesystem server arguments before
using the agent with sensitive sites or files. The filesystem server
should only receive access to the intended sandbox directory.

### 5. Run the app

``` bash
uv run app.py
```

The app is configured to open the Gradio interface in your browser.

## 🔐 Safety notes

Sidekick can interact with tools that have real-world effects. Use it
carefully:

-   Review tool permissions and MCP server configuration before running
    tasks.
-   Keep secrets in environment variables; never commit them.
-   Approve only actions you understand and intend to perform.
-   Use a dedicated test browser profile and non-sensitive sample
    documents during development.
-   Do not assume evaluator feedback, PII middleware, or human approval
    makes every action safe.
-   Verify external actions yourself when correctness matters.

## 🧪 Troubleshooting

**The Go button stays disabled**\
Wait for setup to finish. If it remains disabled, check the terminal for
model credentials, dependency, and MCP startup errors.

**MCP tools fail to load**\
Check that `node` and `npx` are installed, network access is available,
and your installed `langchain-mcp-adapters` version supports the session
APIs used by the project.

**OpenRouter requests fail**\
Verify `OPENROUTER_API_KEY`, the configured model identifier, and the
model's availability and limits in your OpenRouter account.

**Serper or Pushover does not work**\
Check the relevant environment variables and service credentials.

**The app behaves differently after package upgrades**\
Pin and test compatible versions of Gradio, LangChain, LangGraph, and
`langchain-mcp-adapters`. Successful Python syntax compilation does not
guarantee runtime compatibility.

## 🛣️ Possible next steps

-   Add automated tests for the worker/evaluator loop and
    approval/resume flow.
-   Add explicit approve, reject, and edit choices where appropriate.
-   Add structured logging and tracing for tool calls and evaluator
    decisions.
-   Add integration tests for MCP startup, shutdown, and failure
    recovery.
-   Improve document ingestion and add OCR if needed.
-   Add clearer session status and error messages to the UI.

## 🤝 Contributing

Issues, bug reports, and practical improvements are welcome. When
reporting a bug, include:

1.  Python and dependency versions.
2.  The command you ran.
3.  A redacted error traceback.
4.  Relevant MCP configuration with all secrets removed.

## 📄 License

No license has been specified here. Add a `LICENSE` file before
presenting the repository as open source, and choose a license that
matches how you want others to use the project.

------------------------------------------------------------------------

::: {align="center"}
**Sidekick** · Plan clearly. Act carefully. Keep a human in the loop.
:::
