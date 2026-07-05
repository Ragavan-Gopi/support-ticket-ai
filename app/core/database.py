import sqlite3
import logging
from typing import Optional
from app.config import DB_PATH

logger = logging.getLogger(__name__)

def get_db_connection() -> Optional[sqlite3.Connection]:
    """Establishes and returns a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"DB_CONN_ERROR: Failed to connect to database at {DB_PATH}. Details: {e}")
        return None

def init_db() -> bool:
    """Initializes the database schema if it doesn't exist."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        # Create tickets table based on CSV structure
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                created_at TEXT,
                category TEXT,
                priority TEXT,
                status TEXT,
                response_time_hrs REAL,
                resolution_time_hrs REAL,
                agent_id TEXT,
                customer_rating INTEGER,
                issue_summary TEXT
            )
        ''')
        conn.commit()
        logger.info("DB_INIT_SUCCESS: Database schema initialized successfully.")
        return True
    except sqlite3.Error as e:
        logger.error(f"DB_INIT_ERROR: Failed to initialize database schema. Details: {e}")
        return False
    finally:
        conn.close()

def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    """Executes a SELECT query and returns all rows as a list of dictionaries."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"DB_QUERY_ERROR: Failed to execute query. Details: {e}")
        return []
    finally:
        conn.close()
