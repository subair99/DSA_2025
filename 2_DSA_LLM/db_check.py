import os
import sys
import sqlite3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def query_sqlite_database(db_file: str, table_name: str, limit: int = 4):
    """
    Connects to a SQLite database and queries the specified table,
    displaying the first 'limit' rows.
    """
    conn = None
    try:
        print(f"\nAttempting to query SQLite database: {db_file}")
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()

        # Construct the SQL query to select from the table with a LIMIT
        query = f"SELECT * FROM {table_name} LIMIT {limit};"
        print(f"Executing query: {query}")

        cur.execute(query)
        rows = cur.fetchall() # Fetch all results

        # Get column names from the cursor description
        column_names = [description[0] for description in cur.description]

        print(f"\n--- First {limit} rows from '{table_name}' table ---")
        if not rows:
            print("No data found in the table.")
        else:
            # Print column headers
            print("| " + " | ".join(column_names) + " |")
            print("|" + "---|" * len(column_names)) # Separator line

            # Print each row
            for row in rows:
                print("| " + " | ".join(map(str, row)) + " |")
        print("---------------------------------------")

    except sqlite3.Error as e:
        print(f"❌ SQLite query error: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred during query: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()
            print("SQLite query connection closed.")


if __name__ == "__main__":
    # Get SQLite database file path from environment variables.
    sqlite_db_file = os.getenv("DATABASE", "db_agents.db") # Default to db_agents.db

    if not sqlite_db_file:
        print("❌ Error: DATABASE environment variable not set for SQLite file.")
        print("Please set it in your .env file (e.g., DATABASE='db_agents.db')")
        sys.exit(1)

    # Query the database to show the first 4 lines from the 'users' table
    # Assuming your table name is 'users'. Adjust if it's different.
    query_sqlite_database(sqlite_db_file, table_name="users", limit=4)

    print(f"\n🎉 Query operation complete for {sqlite_db_file}.")
