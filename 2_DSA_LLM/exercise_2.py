from langchain.tools import tool, Tool
from langchain.agents import initialize_agent, AgentType
from langchain_community.utilities import SQLDatabase
from model import llm
import os
import re
from dotenv import load_dotenv
import sys

load_dotenv()


# PostgreSQL connection URI
postgres_uri = os.getenv("POSTGRES_URL")
db = SQLDatabase.from_uri(postgres_uri)

# Clean SQL query
def clean_and_run_sql(query: str) -> str:
    query = re.sub(r"```sql|```", "", query).strip()
    result = db.run(query) 
    return result


# Tool 1: Run SQL Query
sql_tool = Tool(
    name="SQL Query Executor",
    func=clean_and_run_sql,
    description="Executes SQL or POSTGRES queries and retrieves results."
)


# Tool 2: Read a file
@tool
def ReadFile(file_name: str) -> str:
    """Reads the contents of a file."""
    try:
        path = os.path.join("filepath", file_name)
        if not os.path.exists(path):
            return f"Error: The file '{file_name}' does not exist."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


# Tool 3: Query DB and write to file
@tool
def WriteQueryResultToFile(query: str) -> str:
    """
    Executes SQL or POSTGRES queries and retrieves results from PostgreSQL and writes the result to 'filepath/<filename>'.
    Creates the directory and file if they do not exist.
    """
    filename = "query_result.txt"
    try:
        # Clean & run SQL
        result = clean_and_run_sql(query)
        
        # Create dir if it doesn't exist
        output_dir = "filepath"
        os.makedirs(output_dir, exist_ok=True)
        
        # Write result to file
        file_path = os.path.join(output_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"This is the result of the query: {result}")
            print("\n")
            sys.exit()
    except Exception as e:
        return f"Failed to write query result: {str(e)}"

# List of tools
tools = [sql_tool, ReadFile, WriteQueryResultToFile]

# Agent setup
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Example usage
response = agent.invoke("How many users are there in the database and write it to a file")
print(response)




# note that ZERO_SHOT_REACT_DESCRIPTION Functions only take one inputs
