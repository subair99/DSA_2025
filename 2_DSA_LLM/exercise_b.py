
import os
import sys

print(f"--- Environment Check ---")
print(f"Current working directory: {os.getcwd()}")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"sys.path (import search paths):")
for p in sys.path:
    print(f"  - {p}")
print(f"-------------------------")


import re
import getpass
import warnings
import operator
from dotenv import load_dotenv
from typing import TypedDict, List, Tuple, Annotated, Union

# LangChain and LangGraph imports
from langchain_groq import ChatGroq
from langchain.tools import tool, Tool
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import ToolInvocation
from langgraph.prebuilt import ToolExecutor
from langgraph.graph import StateGraph, END

# --- Warning Suppression ---
# This is the most effective way to suppress the specific LangChain deprecation warning
warnings.filterwarnings("ignore", message=".*LangChain agents will continue to be supported.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)


# Load environment variables from .env file
load_dotenv()

# --- LLM Initialization ---
def initialize_groq_llm():
    """Initialize GROQ LLM with error handling and model fallback."""
    
    try:
        # ChatGroq is the LLM client, not a LangGraph specific import here
        pass 
    except ImportError:
        print("❌ langchain_groq not installed. Run: pip install langchain-groq")
        return None
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠️ GROQ_API_KEY not found in environment variables")
        api_key = getpass.getpass("Enter your GROQ_API_KEY: ")
        if not api_key:
            print("❌ No API key provided")
            return None
    
    if not api_key.startswith("gsk_"):
        print("⚠️ Warning: API key should start with 'gsk_'")
    
    models_to_try = [
        "llama3-8b-8192", 
        "llama3-70b-8192",
        "gemma-7b-it",
    ]
    
    for model in models_to_try:
        try:
            print(f"🧪 Trying model: {model}")
            llm_instance = ChatGroq(
                model=model,
                temperature=0,
                max_tokens=None,
                timeout=60,
                max_retries=3,
                groq_api_key=api_key
            )
            # Test with a simple message to confirm connectivity
            llm_instance.invoke("Hi")
            print(f"✅ Success! Using model: {model}")
            return llm_instance
            
        except Exception as e:
            print(f"❌ Failed with {model}: {str(e)}")
            continue
    
    print("❌ All models failed. Please check your API key and try again.")
    return None

# Initialize the LLM at module level so it can be imported by the agent
llm = initialize_groq_llm()

# Exit if LLM initialization fails, as the agent cannot function without it
if llm is None:
    print("❌ LLM initialization failed. Exiting.")
    sys.exit(1)

print("✅ Successfully imported LLM from model")

# --- SQLite Connection Setup ---
sqlite_db_file = os.getenv("DATABASE") # Get the DB file name from .env

if not sqlite_db_file:
    print("❌ DATABASE environment variable not set. Cannot connect to SQLite database.")
    sys.exit(1)

sqlite_uri = f"sqlite:///{sqlite_db_file}"

try:
    db = SQLDatabase.from_uri(sqlite_uri)
    print(f"✅ Successfully connected to SQLite database: {sqlite_db_file}")
except Exception as e:
    print(f"❌ Failed to connect to SQLite: {e}")
    sys.exit(1)


# --- Tool Definitions ---

def clean_and_run_sql(query: str) -> str:
    """Cleans an SQL query string and executes it against the database.
    Returns a string representation of the results or an error message.
    """
    query = re.sub(r"```sql|```", "", query).strip()
    try:
        if query.lower().startswith("select"):
            result = db.run(query)
            
            if isinstance(result, list):
                if result:
                    if len(result) == 1 and isinstance(result[0], tuple) and len(result[0]) == 1:
                        return str(result[0][0])
                    else:
                        return ", ".join(str(row) for row in result)
                else:
                    return "No results found for the query."
            else:
                return str(result)

        else:
            result = db.run(query)
            return f"Query executed successfully. Result: {result if result is not None else 'N/A'}"

    except Exception as e:
        return f"SQL execution error: {str(e)} for query: {query}"


sql_tool = Tool(
    name="SQL_Query_Executor", # Renamed for clarity in tool calling
    func=clean_and_run_sql,
    description="Executes SQL or POSTGRES queries and retrieves results. Input should be a complete and valid SQL query string (e.g., 'SELECT * FROM users;')."
)


@tool
def WriteQueryResultToFile(input_string: str) -> str:
    """
    Executes an SQL query and writes the result to 'db_result.txt'
    in the same directory as the SQLite database.
    The input string MUST contain the SQL query to be executed, prefixed with 'SQL:'.
    Example input: "SQL: SELECT COUNT(*) FROM users;".
    Creates the file if it does not exist.
    """
    filename = "db_result.txt"
    try:
        match = re.search(r"SQL:\s*(SELECT.*)", input_string, re.IGNORECASE | re.DOTALL)
        if not match:
            return "Error: Input to WriteQueryResultToFile must start with 'SQL:' followed by the query."
        
        sql_query = match.group(1).strip()
        
        result = clean_and_run_sql(sql_query)
        
        output_dir = os.path.dirname(os.path.abspath(sqlite_db_file))
        os.makedirs(output_dir, exist_ok=True)
        
        file_path = os.path.join(output_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"The number of users is: {result}")
            
        return f"Query result successfully written to {file_path}. Result: {result}"
    except Exception as e:
        return f"Failed to write query result: {str(e)}"


@tool
def ReadFile(file_name: str) -> str:
    """Reads the contents of a file. Input should be the exact file name (e.g., 'report.txt')."""
    try:
        base_dir = os.path.dirname(os.path.abspath(sqlite_db_file))
        path = os.path.join(base_dir, file_name)
        
        if not os.path.exists(path):
            return f"Error: The file '{file_name}' does not exist at '{path}'."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
        

# List of tools for the agent
tools = [sql_tool, WriteQueryResultToFile, ReadFile]

# Initialize ToolExecutor with all tools
tool_executor = ToolExecutor(tools)

# --- LangGraph Agent State Definition ---
# This defines the state schema for our graph.
# 'intermediate_steps' is where (AgentAction, Observation) pairs will be stored.
# `operator.add` means new items returned for this key will be appended.
class AgentState(TypedDict):
    input: str
    chat_history: List[BaseMessage]
    intermediate_steps: Annotated[List[Tuple[AgentAction, str]], operator.add]
    agent_outcome: Union[AgentAction, AgentFinish, None] # To hold the LLM's decision

# --- LangGraph Nodes ---

# 1. Agent Node (Calls LLM to decide next action)
def run_agent(state: AgentState) -> dict:
    """
    Node that runs the LLM to determine the next action (tool call or final answer).
    Parses the LLM's ReAct-style output.
    """
    current_input = state["input"]
    chat_history = state.get("chat_history", [])
    intermediate_steps = state.get("intermediate_steps", [])

    # Format tools for the LLM prompt
    tool_names = ", ".join([t.name for t in tools])
    tool_descriptions = "\n".join([f"{t.name}: {t.description}" for t in tools])

    # Format intermediate steps into a ReAct scratchpad
    agent_scratchpad = ""
    if intermediate_steps:
        # LangGraph appends (AgentAction, Observation) tuples
        formatted_steps = []
        for action, observation in intermediate_steps:
            formatted_steps.append(f"Thought: {action.log.strip()}\nObservation: {observation.strip()}")
        agent_scratchpad = "\n".join(formatted_steps)

    # ReAct prompt template (mimicking ZERO_SHOT_REACT_DESCRIPTION)
    react_prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a helpful AI assistant. You have access to the following tools: {tool_names}\n"
            "{tool_descriptions}\n"
            "Answer the user's question by making use of the available tools. "
            "If you are asked to write a query result to a file, ensure you use the WriteQueryResultToFile tool, "
            "and the input should be 'SQL: <your_sql_query>'. If you are asked to read a file, use the ReadFile tool. "
            "Strictly follow the Thought/Action/Action Input/Observation format. "
            "If you have the final answer, output it in the 'Final Answer:' format."
            "\n\nBegin!"
        )),
        MessagesPlaceholder("chat_history"), # For conversational memory
        ("user", "{input}"),
        ("user", "{agent_scratchpad}"), # Agent's internal monologue
    ])

    # Construct the full prompt
    full_prompt = react_prompt.format_messages(
        input=current_input,
        tool_names=tool_names,
        tool_descriptions=tool_descriptions,
        chat_history=chat_history,
        agent_scratchpad=agent_scratchpad
    )
    
    # Invoke the LLM
    llm_response = llm.invoke(full_prompt)
    response_content = llm_response.content

    print(f"\n--- LLM Response (Run Agent Node) ---\n{response_content}\n-----------------------------------\n")

    # Parse LLM's ReAct output
    action_match = re.search(r"Action:\s*(.*?)\nAction Input:\s*(.*)", response_content, re.DOTALL)
    final_answer_match = re.search(r"Final Answer:\s*(.*)", response_content, re.DOTALL)

    if action_match:
        tool_name = action_match.group(1).strip()
        tool_input = action_match.group(2).strip().strip('"') # Remove quotes if any
        log = response_content
        action = AgentAction(tool=tool_name, tool_input=tool_input, log=log)
        return {"agent_outcome": action}
    elif final_answer_match:
        final_answer = final_answer_match.group(1).strip()
        finish = AgentFinish(return_values={"output": final_answer}, log=response_content)
        return {"agent_outcome": finish}
    else:
        # Fallback for malformed LLM output: treat as a final answer
        print(f"⚠️ Warning: LLM output did not match ReAct format. Treating as final answer.")
        finish = AgentFinish(return_values={"output": response_content}, log=response_content)
        return {"agent_outcome": finish}

# 2. Tool Node (Executes the tool identified by the agent)
def execute_tools(state: AgentState) -> dict:
    """
    Node that executes the tool specified by the agent_outcome.
    Updates the intermediate_steps with the tool's observation.
    """
    agent_action = state["agent_outcome"] # Get the action from the previous node's output
    
    # Prepare ToolInvocation for the ToolExecutor
    tool_invocation = ToolInvocation(tool=agent_action.tool, tool_input=agent_action.tool_input)
    
    # Execute the tool
    try:
        observation = tool_executor.invoke(tool_invocation)
    except Exception as e: # Catch any error from tool execution
        observation = f"Tool Execution Error for tool '{agent_action.tool}' with input '{agent_action.tool_input}': {str(e)}"
        print(f"❌ {observation}")
    
    print(f"\n--- Tool Execution Observation ---\nTool: {agent_action.tool}\nInput: {agent_action.tool_input}\nObservation: {observation}\n----------------------------------\n")
    
    # Return a dictionary that will update the state.
    # The (action, observation) pair is appended to intermediate_steps.
    return {"intermediate_steps": [(agent_action, observation)]}

# --- LangGraph Graph Definition ---

# Define the workflow graph
workflow = StateGraph(AgentState)

# Add nodes to the graph
workflow.add_node("agent", run_agent)        # The LLM decision-making node
workflow.add_node("tools", execute_tools)    # The tool execution node

# Set the entry point of the graph
workflow.set_entry_point("agent")

# Define conditional edges based on the agent's outcome
def route_agent_outcome(state: AgentState) -> str:
    """
    Conditional edge function to determine the next step in the graph
    based on whether the LLM decided to call a tool or provide a final answer.
    """
    if isinstance(state["agent_outcome"], AgentFinish):
        return END # If it's a final answer, end the graph
    else:
        return "tools" # If it's a tool action, go to the 'tools' node

# Add the conditional edge from the 'agent' node
workflow.add_conditional_edges(
    "agent",                 # Source node
    route_agent_outcome,     # Function to determine next node
    {
        END: END,            # If route_agent_outcome returns END, the graph finishes
        "tools": "tools"     # If route_agent_outcome returns "tools", transition to the 'tools' node
    }
)

# After the 'tools' node, always transition back to the 'agent' node
# for the LLM to process the observation and decide the next step (ReAct loop).
workflow.add_edge("tools", "agent")

# Compile the graph into an executable application
app = workflow.compile()

# --- Example Usage ---
if __name__ == "__main__":
    print("\n--- Starting LangGraph Agent Execution ---")

    try:
        # Initial state for the graph.
        # chat_history and intermediate_steps should start empty for a new query.
        initial_state = {
            "input": "Find out how many users are in the database and write the result to a file. The SQL query to count users is 'SELECT COUNT(*) FROM users;'. Use the WriteQueryResultToFile tool with the format 'SQL: <your_sql_query>'.",
            "chat_history": [],
            "intermediate_steps": [],
        }

        # Invoke the LangGraph application
        # The result is the final state of the graph
        final_state = app.invoke(initial_state)

        # The final answer will be in the 'output' key of the AgentFinish object
        # which is stored in agent_outcome when the graph ends.
        agent_output = final_state["agent_outcome"].return_values["output"]
        print(f"\nAgent Response for DB Query: {agent_output}")
        
        # Optional: Read the file to confirm content. Now points to the same directory.
        print("\n--- Attempting to read the written file ---")
        # For reading, we can directly invoke the ReadFile tool since it's a simple operation.
        # Or, we can ask the agent again. Let's ask the agent for consistency.
        read_file_state = app.invoke({
            "input": "Read the file 'db_result.txt'",
            "chat_history": [HumanMessage(content="Read the file 'db_result.txt'")], # Add to history if continuing conversation
            "intermediate_steps": [], # Start fresh for new query
        })
        read_file_content = read_file_state["agent_outcome"].return_values["output"]
        print(f"Content of db_result.txt: {read_file_content}")

    except Exception as e:
        print(f"\n❌ An error occurred during LangGraph agent execution: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        print("\n--- Falling back to direct tool usage due to agent error ---")
        try:
            direct_db_result = clean_and_run_sql('SELECT COUNT(*) FROM users;')
            print(f"Direct DB Query (Count Users): {direct_db_result}")
            
            output_dir = os.path.dirname(os.path.abspath(sqlite_db_file))
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, "db_result.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"This is the direct fallback result: {direct_db_result}")
            print(f"Direct result written to {file_path}")

        except Exception as db_e:
            print(f"Direct DB Query Failed: {db_e}")