#!/usr/bin/env python3
"""
Test script to verify the Web Crawler Search Engine setup.
This script tests the database initialization and basic functionality.
"""

import sqlite3
import sys
import os
from pathlib import Path

def test_database_initialization():
    """Test if the database can be initialized properly."""
    print("Testing database initialization...")
    
    db_path = "crawler.db"
    schema_path = Path(__file__).parent / "schema.sql"
    
    try:
        # Remove existing database for clean test
        if os.path.exists(db_path):
            os.remove(db_path)
            print("✓ Removed existing database")
        
        # Initialize database
        with sqlite3.connect(db_path) as conn:
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())
                conn.commit()
                print("✓ Database schema created successfully")
            else:
                print("✗ Schema file not found")
                return False
        
        # Test basic queries
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'crawl_state', 'hosts', 'pages', 'keywords', 
                'page_keywords', 'crawl_queue', 'robots_cache', 
                'search_history', 'pages_fts'
            ]
            
            missing_tables = set(expected_tables) - set(tables)
            if missing_tables:
                print(f"✗ Missing tables: {missing_tables}")
                return False
            else:
                print("✓ All required tables created")
            
            # Test crawl_state initialization
            cursor.execute("SELECT status FROM crawl_state WHERE id = 1")
            result = cursor.fetchone()
            if result and result[0] == 'stopped':
                print("✓ Crawl state initialized correctly")
            else:
                print("✗ Crawl state not initialized")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

def test_backend_imports():
    """Test if backend modules can be imported."""
    print("\nTesting backend imports...")
    
    backend_dir = Path(__file__).parent / "backend"
    sys.path.insert(0, str(backend_dir))
    
    try:
        from app.core.config import settings
        print("✓ Configuration module imported")
        
        from app.core.database import db_manager
        print("✓ Database manager imported")
        
        from app.services.crawler_service import crawler_service
        print("✓ Crawler service imported")
        
        from app.services.search_service import search_service
        print("✓ Search service imported")
        
        from app.models.schemas import SearchRequest, SearchResponse
        print("✓ Pydantic schemas imported")
        
        return True
        
    except Exception as e:
        print(f"✗ Backend import failed: {e}")
        return False

def test_api_endpoints():
    """Test if API can be initialized."""
    print("\nTesting API initialization...")
    
    try:
        from backend.app.main import app
        print("✓ FastAPI app created")
        
        # Test basic endpoint
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.get("/")
        if response.status_code == 200:
            print("✓ Root endpoint working")
        else:
            print(f"✗ Root endpoint failed: {response.status_code}")
            return False
        
        response = client.get("/health")
        if response.status_code == 200:
            print("✓ Health check endpoint working")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ API initialization failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Web Crawler Search Engine - Setup Test")
    print("=" * 50)
    
    tests = [
        ("Database Initialization", test_database_initialization),
        ("Backend Imports", test_backend_imports),
        ("API Endpoints", test_api_endpoints),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The setup is working correctly.")
        print("\nTo start the application:")
        print("1. Backend: python start_backend.py")
        print("2. Frontend: cd frontend && npm start")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
