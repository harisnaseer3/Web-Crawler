"""Database connection and initialization."""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from .config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and initialization."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.database_path
        self.schema_path = Path(__file__).parent.parent.parent.parent / "schema.sql"
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if self.schema_path.exists():
                    with open(self.schema_path, 'r') as f:
                        conn.executescript(f.read())
                    conn.commit()
                    logger.info("Database initialized successfully")
                else:
                    logger.error(f"Schema file not found at {self.schema_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()):
        """Execute a query and return results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = ()):
        """Execute an update query."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount


# Global database manager instance
db_manager = DatabaseManager()

