#!/usr/bin/env python3
"""
Startup script for the Web Crawler Search Engine backend.
This script initializes the database and starts the FastAPI server.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def initialize_database():
    """Initialize the database with the schema."""
    db_path = "crawler.db"
    schema_path = Path(__file__).parent / "schema.sql"
    
    print("Initializing database...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())
                conn.commit()
                print(f"✓ Database initialized successfully: {db_path}")
            else:
                print(f"✗ Schema file not found: {schema_path}")
                return False
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False
    
    return True

def main():
    """Main startup function."""
    print("Web Crawler Search Engine - Backend Startup")
    print("=" * 50)
    
    # Initialize database
    if not initialize_database():
        print("Failed to initialize database. Exiting.")
        sys.exit(1)
    
    # Start the FastAPI server
    print("\nStarting FastAPI server...")
    print("API will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        import uvicorn
        # Use import string so reload works properly
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except Exception as e:
        print(f"\nError starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
