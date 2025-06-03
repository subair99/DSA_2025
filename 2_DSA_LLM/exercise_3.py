import os
import requests
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOllama
from langchain.tools import Tool
from model import llm
import sys


import warnings
warnings.filterwarnings("ignore")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
GITHUB_API_BASE = "https://api.github.com"


### --- GitHub API Helper Functions --- ###
def search_repositories(query):
    """Search GitHub repositories based on a query."""
    url = f"{GITHUB_API_BASE}/search/repositories?q={query}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        repos = response.json().get("items", [])
        return [f"{repo['full_name']} - {repo['html_url']}" for repo in repos[:5]]
    return f"Error: {response.json()}"


def get_repo_details(repo_name):
    """Fetch details of a specific GitHub repository."""
    url = f"{GITHUB_API_BASE}/repos/{repo_name}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        repo = response.json()
        return f"Repo: {repo['full_name']}\nDescription: {repo['description']}\nStars: {repo['stargazers_count']}\nURL: {repo['html_url']}"
    return f"Error: {response.json()}"


def create_issue(repo_name, title, body=""):
    """Create an issue in a specified GitHub repository."""
    url = f"{GITHUB_API_BASE}/repos/{repo_name}/issues"
    data = {"title": title, "body": body}
    response = requests.post(url, json=data, headers=HEADERS)
    if response.status_code == 201:
        return f"Issue created: {response.json()['html_url']}"
    return f"Error: {response.json()}"



def list_issues(repo_name):
    """List open issues in a repository."""
    url = f"{GITHUB_API_BASE}/repos/{repo_name}/issues"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        issues = response.json()
        return [f"#{issue['number']}: {issue['title']} - {issue['html_url']}" for issue in issues[:5]]
        sys.exit(0)
    return f"Error: {response.json()}"

### --- LangChain Tools --- ###
search_repo_tool = Tool(
    name="GitHub Repository Search",
    func=search_repositories,
    description="Search for GitHub repositories using a keyword."
)

repo_details_tool = Tool(
    name="GitHub Repository Details",
    func=get_repo_details,
    description="Get details of a specific GitHub repository. Input format: 'owner/repo_name'."
)

create_issue_tool = Tool(
    name="GitHub Create Issue",
    func=lambda inputs: create_issue(inputs['repo_name'], inputs['title'], inputs.get('body', '')),
    description="Create a GitHub issue in a repository. Input should be a dictionary with 'repo_name', 'title', and optional 'body'."
)

list_issues_tool = Tool(
    name="GitHub List Issues",
    func=list_issues,
    description="List open issues in a GitHub repository. Input format: 'owner/repo_name'."
)

# List of tools for the agent
tools = [search_repo_tool, repo_details_tool, create_issue_tool, list_issues_tool]


agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

### --- Example Agent Queries --- ###
print(agent.run("Get details about the repository 'langchain-ai/langchain' and list the issues it has"))
