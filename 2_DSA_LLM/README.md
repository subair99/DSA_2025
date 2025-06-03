# 🧠 Agentic AI Exercises

This repository contains three exercises that demonstrate the use of **LangChain agents and tools** to build autonomous systems. These exercises are part of a hands-on training module titled **"Creating with Agentic AI."**

---

## 📦 Project Structure

```
.
├── __pycache__/           # Python bytecode cache
├── filepath/              # Folder to store output files
├── venv/                  # Python virtual environment
├── .env                   # Environment variables (API keys, DB URI)
├── .gitignore             # Git ignore rules
├── exercise_1.py          # Weather tool agent example
├── exercise_2.py          # SQL database + file I/O agent example
├── exercise_3.py          # GitHub integration agent
├── model.py               # LLM setup using LangChain
├── prompt.py              # Custom prompts if any (not used currently)
├── README.md              # 📄 You are here!
└── requirements.txt       # Python dependencies
```

---

## 🧪 Exercises Overview

### ✅ Exercise 1 – Weather Agent

- Uses a tool (`get_weather`) to fetch current weather data using [wttr.in](https://wttr.in)
- **Agent Type**: `ZERO_SHOT_REACT_DESCRIPTION`
- **Example Query**:
  ```python
  "I want to know the weather in New York City"
  ```

---

### ✅ Exercise 2 – SQL + File Writing Agent

This exercise demonstrates how an agent can interact with a PostgreSQL database and write query results to a file.
- Connects to a PostgreSQL database using the environment variable `POSTGRES_URL`.

- The agent connects to a PostgreSQL database using the environment variable:  
  ```env
  POSTGRES_URL=your_postgres_connection_string
  ```

- You can use a hosted database service like [Neon on Vercel](https://vercel.com/integrations/neon-postgres) to quickly set up a free demo database.

---

#### 🧱 Required Table: `users`

Before running the agent, ensure your database contains a table named `users` with some sample data. You can create it with the following SQL:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    age INTEGER,
    city VARCHAR(50)
);
```

**Insert Sample Data:**

```sql
INSERT INTO users (name, email, age, city) VALUES
('Aisha Bello', 'aisha@example.com', 28, 'Lagos'),
('James Okoro', 'james@example.com', 35, 'Abuja'),
('Nkechi Obi', 'nkechi@example.com', 22, 'Enugu'),
('Chinedu Oko', 'chinedu@example.com', 30, 'Owerri'),
('Fatima Ahmed', 'fatima@example.com', 26, 'Kano'),
('Ibrahim Musa', 'ibrahim@example.com', 40, 'Kaduna'),
('Blessing Udo', 'blessing@example.com', 32, 'Uyo'),
('Tolu Adebayo', 'tolu@example.com', 27, 'Ibadan'),
('Ngozi Chika', 'ngozi@example.com', 24, 'Asaba'),
('Emeka Eze', 'emeka@example.com', 29, 'Onitsha');
```

---




**Tools Used**:
- `SQL Query Executor`: Executes SQL commands  
- `ReadFile`: Reads from a file in `filepath/`  
- `WriteQueryResultToFile`: Executes a query and saves the result to a file

**Example Query**:
```python
"How many users are there in the database and write it to a file"
```

---

### ✅ Exercise 3 – GitHub Agent

- Interacts with the GitHub API using your personal access token.

**Tools Used**:
- `GitHub Repository Search`
- `GitHub Repository Details`
- `GitHub Create Issue`
- `GitHub List Issues`

**Example Query**:
```python
"Get details about the repository 'langchain-ai/langchain' and list the issues it has"
```

---

## ⚙️ Setup Instructions

### 1. Clone this repository

```bash
git clone https://github.com/your-username/agentic-ai-exercises.git
cd agentic-ai-exercises
```
## 2. Install dependencies with UV
#### ⚡ Installing Astral UV

To install **Astral UV**, run the following command in **PowerShell**:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> 📌 This command downloads and installs Astral UV using PowerShell by bypassing execution policy and executing the remote script.

---

#### 🛠 Creating a Virtual Environment with UV

Follow the official documentation to create a virtual environment using UV:

🔗 [Astral UV – Managing Python Environments](https://docs.astral.sh/uv/pip/environments/)



### 2. Create a virtual environment and activate it

```bash
python3 -m venv .venv or uv .venv
source venv/bin/activate   or .venv/Scripts/activate # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root directory and add:

```env
POSTGRES_URL=your_postgres_connection_string
GITHUB_TOKEN=your_github_personal_access_token
```

---

## 🚀 Running the Exercises

```bash
# Run Exercise 1 – Weather Agent
python exercise_1.py

# Run Exercise 2 – SQL Agent + File Writer
python exercise_2.py

# Run Exercise 3 – GitHub API Agent
python exercise_3.py
```

---

## 🛠 LangChain Agent Configuration

All agents are initialized using the `initialize_agent` function from LangChain:

```python
initialize_agent(
    tools=...,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
```

- The **Language Model (`llm`)** is defined in `model.py`
- Tools are defined using `@tool` decorators or created with `Tool()`

---

## 📌 Notes

- Ensure you have internet access for external API calls (e.g., wttr.in, GitHub).
- The `filepath/` directory will be automatically created if it doesn't exist.
- Tool inputs must be either a single string or a dictionary depending on the tool.
- **Do not hardcode credentials** — use the `.env` file for all sensitive data.

---

## ✨ Credits

Built as part of the **LangChain x Agentic AI Engineering Training**.

Inspired by the power of **LLMs, APIs, and Tool-Using Agents**.
