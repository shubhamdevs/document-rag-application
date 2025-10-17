# SQLite compatibility fix for ChromaDB
# This MUST be imported before any chromadb imports
import sys
import os

def fix_sqlite():
    """Fix SQLite version compatibility for ChromaDB"""
    try:
        # Always try to use pysqlite3 for maximum compatibility
        import pysqlite3
        # Replace the sqlite3 module completely
        sys.modules['sqlite3'] = pysqlite3
        print("✅ Fixed SQLite with pysqlite3 for ChromaDB compatibility")
        return True
    except ImportError:
        print("❌ pysqlite3 not available")
        # Check if default sqlite3 is compatible
        import sqlite3
        if sqlite3.sqlite_version < '3.35.0':
            error_msg = f"SQLite version {sqlite3.sqlite_version} < 3.35.0 required by ChromaDB"
            print(f"❌ {error_msg}")
            print("Install pysqlite3: pip install pysqlite3")
            return False
        else:
            print(f"✅ SQLite version {sqlite3.sqlite_version} is compatible")
            return True

# Apply the fix immediately when this module is imported
if not fix_sqlite():
    raise RuntimeError("ChromaDB requires SQLite >= 3.35.0. Please install pysqlite3: pip install pysqlite3")