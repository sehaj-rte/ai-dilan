#!/usr/bin/env python3
"""
Database initialization script for Dilan AI Backend
Run this script to create the database tables
"""

from config.database import create_tables, engine
from models.user_db import UserDB
import sys

def init_database():
    """Initialize the database with all tables"""
    try:
        print("🔄 Creating database tables...")
        
        # Import all models to ensure they're registered with Base
        from models.user_db import UserDB
        from models.expert_db import ExpertDB
        
        # Create all tables
        create_tables()
        
        print("✅ Database tables created successfully!")
        print("📋 Created tables:")
        print("   - users")
        print("   - experts")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
