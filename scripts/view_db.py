"""
Simple CLI script to view contents of data/pipeline.db in terminal.
Usage: python scripts/view_db.py
"""

import sqlite3
import os
import sys

# Ensure UTF-8 output encoding for terminal printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = "data/pipeline.db"


def view_db():
    if not os.path.exists(DB_PATH):
        print(f"[!] Database file '{DB_PATH}' does not exist yet. Run 'python -m src.main' to create it.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all tables using valid SQL standard single-quotes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print(f"--- SQLite Database: '{DB_PATH}' ---")

    for (table_name,) in tables:
        print(f"\n[Table: {table_name}]")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [col[1] for col in cursor.fetchall()]
        print("  Columns: " + " | ".join(columns))
        print("  " + "-" * 40)

        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        if not rows:
            print("  (No rows found)")
        else:
            for row in rows:
                print("  " + str(row))

    conn.close()


if __name__ == "__main__":
    view_db()
