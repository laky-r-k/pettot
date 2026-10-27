"""
migrations/migrate.py
----------------------
Lightweight schema migration runner.
Applies ALTER TABLE changes to an existing SQLite DB without dropping data.

Usage:
    python migrations/migrate.py

Run this once after any model schema change that adds columns.
(For column renames / drops, write a custom migration here.)
"""
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./test.db").replace("sqlite:///", "")


def column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def run_migrations():
    print(f"Running migrations on: {DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # ── Migration 001: Add created_at to subscriptions ────────────────────────
    if not column_exists(cur, "subscriptions", "created_at"):
        cur.execute("ALTER TABLE subscriptions ADD COLUMN created_at DATETIME")
        print("  ✅ Added subscriptions.created_at")
    else:
        print("  ⏭  subscriptions.created_at already exists")

    # ── Add future migrations below this line ─────────────────────────────────
    # if not column_exists(cur, "table_name", "new_column"):
    #     cur.execute("ALTER TABLE table_name ADD COLUMN new_column TEXT")
    #     print("  ✅ Added table_name.new_column")

    con.commit()
    con.close()
    print("Migrations complete.")


if __name__ == "__main__":
    run_migrations()
