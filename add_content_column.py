#!/usr/bin/env python3
"""
Database migration script to add content column to files table
This provides a fallback storage when S3 is not configured
"""

from sqlalchemy import create_engine, text
from config.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_content_column():
    """Add content column to files table as fallback storage"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Check if column already exists
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='files' AND column_name='content'
            """))
            
            if result.fetchone():
                logger.info("✅ Content column already exists in files table")
                return True
            
            # Add the content column
            logger.info("Adding content column to files table...")
            connection.execute(text("""
                ALTER TABLE files 
                ADD COLUMN content BYTEA
            """))
            connection.commit()
            
            logger.info("✅ Successfully added content column to files table")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error adding content column: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Database Migration: Adding content column to files table")
    print("=" * 50)
    print("This column provides fallback storage when S3 is not configured.")
    print("Files will be stored in S3 when available, database otherwise.")
    print()
    
    success = add_content_column()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nHybrid Storage System:")
        print("  - Primary: AWS S3 (when configured)")
        print("  - Fallback: Database (when S3 unavailable)")
        print("\nYou can now upload files and the system will:")
        print("  1. Try to upload to S3")
        print("  2. Fall back to database if S3 fails")
        print("  3. Retrieve from either source during processing")
    else:
        print("\n💥 Migration failed!")
        print("Please check the error messages above.")
