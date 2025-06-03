import os
import sys
import sqlite3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def read_sql_file(file_path: str) -> str:
    """Reads SQL commands from a specified file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print(f"✅ Successfully read SQL from: {file_path}")
        return sql_content
    except FileNotFoundError:
        print(f"❌ Error: SQL file not found at '{file_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading SQL file: {e}")
        sys.exit(1)


def execute_sql_in_sqlite(db_file: str, sql_commands: str):
    """Connects to a SQLite database file and executes the provided SQL commands."""
    conn = None
    try:
        print(f"Attempting to connect to SQLite database: {db_file}")
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()

        # Split commands by ';' to execute them one by one.
        # This handles multiple SQL statements in db_content.txt.
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]

        for command in commands:
            if command:
                print(f"Executing SQL command: {command[:70]}...")
                cur.execute(command)
                conn.commit()
                print("Command executed.")

        print("✅ All SQL commands executed successfully.")

    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if conn:
            cur.close()
            conn.close()
            print("SQLite connection closed.")


if __name__ == "__main__":
    # Get SQLite database file path from environment variables.
    # We use 'DATABASE' from .env for the SQLite file name.
    # A default value 'mydatabase.db' is provided if DATABASE is not set in .env.
    sqlite_db_file = os.getenv("DATABASE", "mydatabase.db")

    if not sqlite_db_file:
        print("❌ Error: DATABASE environment variable not set for SQLite file.")
        print("Please set it in your .env file (e.g., DATABASE='mydatabase.db')")
        sys.exit(1)

    # Define the path to your SQL file
    sql_file_path = 'db_content.txt'

    # Read SQL commands from the file
    sql_content = read_sql_file(sql_file_path)

    # Execute SQL commands in SQLite
    # IMPORTANT: Ensure your db_content.txt uses 'id INTEGER PRIMARY KEY'
    # and either omits 'id' in INSERT statements or inserts NULL.
    execute_sql_in_sqlite(sqlite_db_file, sql_content)

    print(f"\n🎉 Database setup complete (table created and data inserted) in {sqlite_db_file}.")