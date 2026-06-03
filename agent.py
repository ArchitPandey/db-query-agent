from pathlib import Path
from dotenv import load_dotenv

# searches for .env file and loads it into os.environ
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

from typing import Annotated, TypedDict
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langchain_core.messages import AIMessage

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from sqlalchemy import create_engine, text, inspect

# intialize with groq ollma model
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# llm system prompt
SYSTEM_PROMPT = """You are a precise database assistant. 
You must ALWAYS call `get_database_schema` first to inspect the tables and columns before writing a query. 
Do not guess table or column names. Once you see the schema, write a valid SQLite query and run it using `run_sql_query` to get the answer."""

# connect to sqllite db
engine = create_engine("sqlite:///dev_database.db")

# 2. Define the State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    retry_count: int

# 3. Define tools to allow groq to dicover db tables and execute queries
@tool
def get_database_schema() -> str:
    """Use this tool to inspect the database schema and discover table names and columns."""
    inspector = inspect(engine)
    schema_info = []
    for table_name in inspector.get_table_names():
        columns = [f"{col['name']} ({col['type']})" for col in inspector.get_columns(table_name)]
        schema_info.append(f"Table: {table_name}\nColumns: {', '.join(columns)}")
    return "\n\n".join(schema_info)

@tool
def run_sql_query(query: str) -> str:
    """Execute a raw SQL SELECT query against the database and return results as a string."""
    # Simple read-only guardrail
    if any(kw in query.lower() for kw in ["drop", "delete", "insert", "update"]):
        return "Error: Execution denied. Only read-only SELECT queries are allowed."
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            return str([dict(row._mapping) for row in rows])
    except Exception as e:
        return f"SQL Error: {str(e)}"

# Group your tools into a list
tools = [get_database_schema, run_sql_query]

# 4. Bind the tools to our Groq LLM model
# This translates our Python function into JSON schemas the LLM understands.
llm_with_tools = llm.bind_tools(tools)

# Node A: The Agent/LLM Node
def call_model(state: AgentState):
    current_retries = state.get("retry_count", 0)

    if current_retries > 3:
        print(f"\n🛑 Hard Limit Reached! (Retries: {current_retries}). Aborting graph to prevent infinite loop.")
        abort_message = AIMessage(
            content="I apologize, but I encountered repeated database errors that I was unable to resolve automatically. Please verify your query or schema layout."
        )
        return {"messages": [abort_message]}

    response = llm_with_tools.invoke(state["messages"])
    # We return a dictionary updating the 'messages' key in our state
    return {"messages": [response]}

# Node B: The Tools Node
# LangGraph provides a prebuilt ToolNode utility that automatically handles 
# matching the LLM's requested tool calls to the actual Python function execution.
tool_node = ToolNode(tools)
def custom_tool_node(state: AgentState):
    tool_output_state = tool_node.invoke(state)

    latest_tool_msg = tool_output_state["messages"][-1]
    
    if "SQL Error" in latest_tool_msg.content:
        current_retries = state.get("retry_count", 0)
        print(f"\n⚠️ Database reported an error! Incrementing retry count to {current_retries + 1}...")
        tool_output_state["retry_count"] = current_retries + 1
    return tool_output_state

# 5. Define Conditional Routing Edge
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    
    # If the LLM output contains 'tool_calls', we must route to the tool node
    if last_message.tool_calls:
        return "tools"
    
    # If there are no tool calls, the agent has formed its final answer. Stop execution.
    return "__end__"

# 6. Initialize the graph canvas with our State schema
workflow = StateGraph(AgentState)

# Add our active nodes to the canvas
workflow.add_node("agent", call_model)
workflow.add_node("tools", custom_tool_node)

# Map out the flow of connections
workflow.add_edge(START, "agent")  # Always start execution at the agent node

# The agent node branches conditionally based on what 'should_continue' returns
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",       # If it returns "tools", route execution to Node B
        "__end__": "__end__"    # If it returns "__end__", stop the whole graph
    }
)

# After tools finish executing, they always loop back to the agent for validation
workflow.add_edge("tools", "agent")

# Compile the graph into a standard executable LangChain Runnable
app = workflow.compile()

# 7. Test it out
if __name__ == "__main__":
    print("🤖 Database Agent Initialized. Type 'exit' or 'quit' to stop.\n")
    
    while True:
        # Capture dynamic user input from the terminal
        user_query = input("You: ")
        
        # Guard clause to break out of the infinite loop
        if user_query.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
            
        # Skip empty inputs
        if not user_query.strip():
            continue
            
        # Pass the dynamic input straight into your initial graph state
        initial_input = {
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                ("user", user_query)
            ]
        }
    
        print("\n--- Agent Thinking ---")
        for event in app.stream(initial_input, stream_mode="values"):
            # This will print the status of the messages array at every single step of the graph
            last_msg = event["messages"][-1]
            last_msg.pretty_print()
