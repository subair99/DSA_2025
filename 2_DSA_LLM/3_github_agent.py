import os
import sys
import requests
import json
from dotenv import load_dotenv
from model import llm # Assuming 'llm' is properly defined in 'model.py'
from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_react_agent
from langchain import hub

import warnings
warnings.filterwarnings("ignore")

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
GITHUB_API_BASE = "https://api.github.com"

# Check if GITHUB_TOKEN is set
if not GITHUB_TOKEN:
    print("Error: GITHUB_TOKEN environment variable not set.")
    print("Please set it before running the script (e.g., export GITHUB_TOKEN='YOUR_TOKEN').")
    sys.exit(1)


# Import LLM from model
try:
    from model import llm
    if llm is None:
        raise ValueError("LLM initialization failed in model.py")
    print("✅ Successfully imported LLM from model")
except Exception as e:
    print(f"❌ Error importing LLM: {e}")
    exit(1)


### --- Define tools with @tool decorator --- ###
@tool
def search_repositories(query: str) -> str:
    """Search GitHub repositories based on a keyword or phrase.
    This tool is useful when you need to find repositories matching a general term.
    Example: search_repositories(query='python web framework')
    Example: search_repositories(query='LLM agents')
    """
    url = f"{GITHUB_API_BASE}/search/repositories?q={query}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        repos = response.json().get("items", [])
        if not repos:
            return f"No repositories found for query: {query}"
        # Return only the full_name and html_url for the agent to easily parse
        return "\n".join([f"Repo: {repo['full_name']}, URL: {repo['html_url']}" for repo in repos[:5]])
    return f"Error: {response.json()}"


@tool
def get_repo_details(repo_name: str) -> str:
    """Get comprehensive details about a specific GitHub repository.
    The input `repo_name` MUST be a string in the exact 'owner/repo_name' format (e.g., 'microsoft/vscode', 'langchain-ai/langchain').
    This tool is crucial for obtaining information like description, stars, forks, and language of a known repository.
    Example: get_repo_details(repo_name='microsoft/vscode')
    """
    url = f"{GITHUB_API_BASE}/repos/{repo_name}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        repo = response.json()
        return f"Repo: {repo['full_name']}\nDescription: {repo['description']}\nStars: {repo['stargazers_count']}\nForks: {repo['forks_count']}\nLanguage: {repo['language']}\nURL: {repo['html_url']}"
    if response.status_code == 404:
        return f"Error: Repository '{repo_name}' not found. Please ensure the format is 'owner/repo_name'."
    return f"Error fetching details for {repo_name}: {response.json()}"


@tool
def create_issue(input_str: str) -> str:
    """Create a GitHub issue in a repository.
    Input must be a JSON string with 'repo_name', 'title', and optional 'body' keys.
    The 'repo_name' MUST be in 'owner/repo' format.
    Example: create_issue(input_str='{"repo_name": "my_owner/my_repo", "title": "Bug: Fix broken link", "body": "The link in README.md is broken."}')
    """
    try:
        data = json.loads(input_str)
        repo_name = data['repo_name']
        title = data['title']
        body = data.get('body', '')
    except (json.JSONDecodeError, KeyError):
        return "Error: Input should be JSON format like {'repo_name': 'owner/repo', 'title': 'Issue title', 'body': 'Issue body'}"
    
    url = f"{GITHUB_API_BASE}/repos/{repo_name}/issues"
    data = {"title": title, "body": body}
    response = requests.post(url, json=data, headers=HEADERS)
    if response.status_code == 201:
        return f"Issue created: {response.json()['html_url']}"
    return f"Error creating issue in {repo_name}: {response.json()}"


@tool
def list_issues(repo_name: str) -> str:
    """List the open issues for a given GitHub repository.
    The input `repo_name` MUST be a string in the exact 'owner/repo_name' format (e.g., 'microsoft/vscode', 'tensorflow/tensorflow').
    Use this tool to see ongoing discussions or bugs for a specific project.
    Example: list_issues(repo_name='microsoft/vscode')
    """
    url = f"{GITHUB_API_BASE}/repos/{repo_name}/issues"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        issues = response.json()
        if not issues:
            return f"No open issues found in {repo_name}"
        issue_list = []
        for issue in issues[:5]: # Limit to top 5 issues for brevity
            issue_list.append(f"#{issue['number']}: {issue['title']} - {issue['html_url']}")
        return "\n".join(issue_list)
    if response.status_code == 404:
        return f"Error: Repository '{repo_name}' not found. Please ensure the format is 'owner/repo_name'."
    return f"Error listing issues for {repo_name}: {response.json()}"


# List of tools for the agent
tools = [search_repositories, get_repo_details, create_issue, list_issues]
print("🤖 GitHub Agent initialized successfully!")


# Try different agent approaches
def create_agent_with_fallback():
    """Try different agent creation methods"""
    
    # Method 1: Tool calling agent (preferred)
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Use the available tools to answer questions."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_tool_calling_agent(llm, tools, prompt)
        
        # Set verbose=True for debugging
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True) 
        
        print("✅ Tool calling agent created successfully!")
        return agent_executor
        
    except Exception as e:
        print(f"⚠️ Tool calling agent failed: {e}")
    

    # Method 2: React agent (fallback)
    try:
        # Get react prompt
        prompt = hub.pull("hwchase17/react")
        agent = create_react_agent(llm, tools, prompt)
        
        # Set verbose=True
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        print("✅ React agent created successfully!")
        return agent_executor
        
    except Exception as e:
        print(f"⚠️  React agent failed: {e}")
    

    # Method 3: Legacy agent (last resort)
    try:
        # Set verbose=True
        agent_executor = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True
        )
        
        print("✅ Legacy agent created successfully!")
        return agent_executor
        
    except Exception as e:
        print(f"❌ Legacy agent failed: {e}")
        return None


# --- Example Usage ---
if __name__ == "__main__":
    print("\n--- Starting GitHub Agent Execution ---")

    agent_executor = create_agent_with_fallback()

    query = """
    First, search for GitHub repositories related to 'microsoft/vscode'.
    From the search results, identify the main 'microsoft/vscode' repository.
    Then, get detailed information about that specific 'microsoft/vscode' repository.
    Finally, list the open issues for the 'microsoft/vscode' repository.
    Please ensure you use the exact 'owner/repo_name' format when calling tools that require it.
    """

    if agent_executor:
        try:
            result_search = agent_executor.invoke({"input": query})
            print(f"\nFinal Result: {result_search['output']}")
            
        except Exception as e:
            print(f"❌ Error running agent: {str(e)}")
            print(f"Error type: {type(e).__name__}")