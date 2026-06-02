# LangGraph SQLite Database Agent

A lightweight, local AI agent built with **LangGraph** and **Groq** (`llama-3.3-70b-versatile`) that dynamically reads an unknown database schema, generates accurate SQLite queries, executes them safely, and translates raw data rows into friendly, conversational answers.

The project leverages **`uv`** for lightning-fast, reproducible dependency and environment management.

---

## Technical Concept: How It Works

This application is built as an explicit state machine (a Graph) rather than a black-box chain. Instead of hardcoding steps, the graph orchestrates an intelligent routing loop between the LLM and your local system tools.

[User Query] ──> [Agent Node] ──(wants schema)──> [get_database_schema]
▲                                  │
│─────────(returns columns)────────┘
▼
[Agent Node] ──(wants data)────> [run_sql_query]
▲                                  │
│──────────(returns rows)──────────┘
▼
[Final Answer]

1. **The State (`AgentState`):** A shared conversation history wrapper managed by LangGraph using an `add_messages` reducer to automatically append step logs without overwriting historical turns.
2. **The Discovery Phase (`get_database_schema`):** The agent reads your strict system prompt constraints and realizes it has zero awareness of your tables. It triggers the schema extraction tool to read the columns dynamically.
3. **The Execution Phase (`run_sql_query`):** The agent consumes the structural metadata returned by the schema tool, constructs an exact matching SQLite syntax statement, routes to the query execution block, and formats the raw matrix output into plain text.

---

## Prerequisites

Before setting up the project, ensure you have **Python 3.10+** and **uv** installed. 

If you do not have `uv` installed, run the appropriate command for your OS:

```bash
# macOS/Linux
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

# Windows (PowerShell)
powershell -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"
```


## Project Structure
├── .env                # Local environment configuration (Secrets)
├── agent.py            # Main LangGraph engine and conversational CLI loop
├── init_db.py          # Database initializer and sample data seed script
├── pyproject.toml      # Project manifest managing uv package specifications
└── dev_database.db     # The generated local SQLite database file

## Setup Instructions
1. Configure Secrets
Create a .env file in the root of your project directory and add your Groq API key:
```bash
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

2. Lock Down Dependencies
Sync your local workspace virtual environment package ecosystem instantly with uv:
```bash
uv sync
```

## How to run this project
Follow these steps sequentially to build your local sandbox environment and launch the AI agent.

Step 1: Initialize and Seed the SQLite Database
Run the database builder script to instantiate your customers and orders tables:
```bash
uv run init_db.py
```

Step 2: Launch the Conversational Agent
Once your database file is fully generated, start the interactive runtime loop using the --env-file flag to safely load your secrets directly into the shell space:
```bash
uv run --env-file .env agent.py
```

## Sample Testing Scenarios
Type these scenarios directly into your active console session to evaluate the agent's reasoning capabilities:

1. Basic Metadata Inquiries
"Which country is our customer Amit Sharma from?"

"How many customers do we have listed in the system?"

2. Aggregations and Grouping
"List all customers who joined the platform after February 2026."

"What is the total count of orders placed in our system?"

3. Cross-Table Structural Joins
"What items did Amit Sharma purchase, and how much did he spend in total?"

"Can you show me the name of the customer who ordered the Mechanical Keyboard?"

4. Verification of Read-Only Guardrails
"DELETE FROM orders WHERE order_id = 101;"
(Expected behavior: The script's internal execution block will catch the destructive SQL keyword constraint, reject the submission, and return an explicit safety error block instead of running the command).

## Exit the Application
To terminate your interactive terminal engine session cleanly, simply type exit or quit into the terminal prompt input field.
