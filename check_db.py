"""Utility for inspecting the application database state and contents."""

import os
import sqlite3

db_path = "python-server/app.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables in database: {tables}")

    # Check each table for data
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"Table '{table_name}' has {count} rows")

        # Show first few rows if any data exists
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            rows = cursor.fetchall()
            print(f"Sample data from '{table_name}':")
            for row in rows:
                print(f"  {row}")

    conn.close()
else:
    print("Database file does not exist")
