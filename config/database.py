import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/dilan_ai_db")

# Remove channel_binding parameter if present (causes issues with some PostgreSQL versions)
if "channel_binding=require" in DATABASE_URL:
    print("⚠️  Removing channel_binding=require from DATABASE_URL")
    DATABASE_URL = DATABASE_URL.replace("&channel_binding=require", "").replace("channel_binding=require&", "").replace("?channel_binding=require", "")
    print(f"✅ Updated DATABASE_URL (password hidden)")

print(f"🔌 Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")

# Create SQLAlchemy engine with connection pool settings
# Note: We explicitly disable channel_binding in connect_args to avoid bcrypt 72-byte limit issues
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=3600,   # Recycle connections after 1 hour
        connect_args={
            "connect_timeout": 10,
            "options": "-c timezone=utc",
            "channel_binding": "disable"  # Explicitly disable channel binding
        }
    )
    print("✅ Database engine created successfully")
except Exception as e:
    print(f"❌ Error creating database engine: {e}")
    # Fallback: try without channel_binding parameter
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "connect_timeout": 10,
            "options": "-c timezone=utc"
        }
    )
    print("✅ Database engine created with fallback configuration")

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Metadata for table creation
metadata = MetaData()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all tables"""
    Base.metadata.drop_all(bind=engine)
