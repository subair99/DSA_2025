import os
import getpass
from dotenv import load_dotenv
import sys
import re
import warnings

# --- Warning Suppression ---
# This is the most effective way to suppress the specific LangChain deprecation warning
# It targets the exact message string.
warnings.filterwarnings("ignore", message=".*LangChain agents will continue to be supported.*")
warnings.filterwarnings("ignore", category=DeprecationWarning) # Catch other DeprecationWarnings too


# Load environment variables from .env file
load_dotenv()

# --- LLM Initialization ---
def initialize_groq_llm():
    """Initialize GROQ LLM with error handling and model fallback."""
    
    try:
        from langchain_groq import ChatGroq
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
from langchain.tools import tool, Tool
from langchain.agents import initialize_agent, AgentType
from langchain_community.utilities import SQLDatabase

# Get SQLite database file path from environment variables
sqlite_db_file = os.getenv("DATABASE") # Get the DB file name from .env

if not sqlite_db_file:
    print("❌ DATABASE environment variable not set. Cannot connect to SQLite database.")
    sys.exit(1)

# Construct the SQLite URI. Langchain's SQLDatabase expects this format for SQLite.
# This assumes the database file is in the same directory as the script.
sqlite_uri = f"sqlite:///{sqlite_db_file}"

try:
    db = SQLDatabase.from_uri(sqlite_uri)
    print(f"✅ Successfully connected to SQLite database: {sqlite_db_file}")
except Exception as e:
    print(f"❌ Failed to connect to SQLite: {e}")
    sys.exit(1)


# --- Tool Definitions ---

# Helper function to clean and run SQL queries
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


# Tool 1: Run SQL Query
sql_tool = Tool(
    name="SQL Query Executor",
    func=clean_and_run_sql,
    description="Executes SQL or POSTGRES queries and retrieves results. Input should be a complete and valid SQL query string (e.g., 'SELECT * FROM users;')."
)


# Tool 2: Query DB and write to file
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
        # Extract the SQL query from the input_string
        match = re.search(r"SQL:\s*(SELECT.*)", input_string, re.IGNORECASE | re.DOTALL)
        if not match:
            return "Error: Input to WriteQueryResultToFile must start with 'SQL:' followed by the query."
        
        sql_query = match.group(1).strip()
        
        result = clean_and_run_sql(sql_query)
        
        # Determine the output directory as the same directory as the SQLite database
        output_dir = os.path.dirname(os.path.abspath(sqlite_db_file))
        os.makedirs(output_dir, exist_ok=True)
        
        # Write result to file
        file_path = os.path.join(output_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"The number of users is: {result}") # Adjusted the output format here
            
        return f"Query result successfully written to {file_path}. Result: {result}"
    except Exception as e:
        return f"Failed to write query result: {str(e)}"


# Tool 3: Read a file
@tool
def ReadFile(file_name: str) -> str:
    """Reads the contents of a file. Input should be the exact file name (e.g., 'report.txt')."""
    try:
        # Determine the base directory for file operations
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


# Agent setup
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True
)


# --- Example Usage ---
if __name__ == "__main__":
    print("\n--- Starting Agent Execution ---")

    try:
        db_task_prompt = "Find out how many users are in the database and write the result to a file. The SQL query to count users is 'SELECT COUNT(*) FROM users;'. Use the WriteQueryResultToFile tool with the format 'SQL: <your_sql_query>'."
        
        response = agent.invoke({"input": db_task_prompt})
        print(f"Agent Response for DB Query: {response['output']}")
        
        # Optional: Read the file to confirm content. Now points to the same directory.
        print("\n--- Attempting to read the written file ---")
        read_file_response = agent.invoke({"input": "Read the file 'db_result.txt'"})
        print(f"Content of db_result.txt: {read_file_response['output']}")

    except Exception as e:
        print(f"\n❌ An error occurred during agent execution: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        print("\n--- Falling back to direct tool usage due to agent error ---")
        try:
            direct_db_result = clean_and_run_sql('SELECT COUNT(*) FROM users;')
            print(f"Direct DB Query (Count Users): {direct_db_result}")
            
            # Manually write to file for fallback, in the same directory as the DB
            output_dir = os.path.dirname(os.path.abspath(sqlite_db_file))
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, "db_result.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"This is the direct fallback result: {direct_db_result}")
            print(f"Direct result written to {file_path}")

        except Exception as db_e:
            print(f"Direct DB Query Failed: {db_e}")