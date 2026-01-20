"""
Database initialization script for Netlify Functions
Run this once to set up the database tables.
Can be run locally or as a one-time Netlify function.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from utils import execute_query

def init_db():
    """Initialize database tables"""
    
    # Create Users table
    execute_query("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create User History table
    execute_query("""
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            date TEXT NOT NULL,
            results TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create User Requirements table
    execute_query("""
        CREATE TABLE IF NOT EXISTS user_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            requirements TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create User Shortlist table
    execute_query("""
        CREATE TABLE IF NOT EXISTS user_shortlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            shortlist TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Add useful indexes for performance
    execute_query("CREATE INDEX IF NOT EXISTS idx_user_history_user_id ON user_history(user_id);")
    execute_query("CREATE INDEX IF NOT EXISTS idx_user_history_date ON user_history(user_id, date);")
    execute_query("CREATE INDEX IF NOT EXISTS idx_requirements_user_id ON user_requirements(user_id);")
    execute_query("CREATE INDEX IF NOT EXISTS idx_shortlist_user_id ON user_shortlist(user_id);")

    print("✅ Database tables initialized successfully")

if __name__ == "__main__":
    init_db()

