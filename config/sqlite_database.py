import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SQLite database configuration (for quick development)
SQLITE_DATABASE_URL = "sqlite:///./dilan_ai.db"

# Create SQLAlchemy engine for SQLite
sqlite_engine = create_engine(SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})

# Create SessionLocal class
SQLiteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)

# Create Base class for models
Base = declarative_base()

# Metadata for table creation
metadata = MetaData()

def get_sqlite_db():
    """Dependency to get SQLite database session"""
    db = SQLiteSessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_sqlite_tables():
    """Create all tables in SQLite"""
    Base.metadata.create_all(bind=sqlite_engine)

def drop_sqlite_tables():
    """Drop all tables in SQLite"""
    Base.metadata.drop_all(bind=sqlite_engine)

# Quick setup function
def setup_sqlite():
    """Quick setup for SQLite database"""
    print("🔄 Setting up SQLite database...")
    try:
        # Import models to register them
        from models.user_db import UserDB
        from models.expert_db import ExpertDB
        from models.file_db import FileDB
        
        # Create tables
        create_sqlite_tables()
        print("✅ SQLite database setup complete!")
        print(f"📁 Database file: {os.path.abspath('dilan_ai.db')}")
        return True
    except Exception as e:
        print(f"❌ SQLite setup failed: {e}")
        return False

if __name__ == "__main__":
    setup_sqlite()
