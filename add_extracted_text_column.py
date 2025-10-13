#!/usr/bin/env python3
"""
Database migration script to add extracted_text column to files table
This stores the full text content extracted from uploaded files
"""

from sqlalchemy import create_engine, text
from config.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_extracted_text_column():
    """Add extracted_text column to files table"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Check if column already exists
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='files' AND column_name='extracted_text'
            """))
            
            if result.fetchone():
                logger.info("✅ extracted_text column already exists in files table")
                return True
            
            # Add the extracted_text column
            logger.info("Adding extracted_text column to files table...")
            connection.execute(text("""
                ALTER TABLE files 
                ADD COLUMN extracted_text TEXT
            """))
            connection.commit()
            
            logger.info("✅ Successfully added extracted_text column to files table")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error adding extracted_text column: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Database Migration: Adding extracted_text column to files table")
    print("=" * 50)
    print("This column stores the full text content extracted from uploaded files.")
    print("It enables faster agent creation by avoiding re-extraction of documents.")
    print()
    
    success = add_extracted_text_column()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nFast Document Processing System:")
        print("  - Text extraction happens during file upload")
        print("  - Full extracted text is stored in database")
        print("  - Agent creation uses pre-extracted text (no re-extraction needed)")
        print("\nBenefits:")
        print("  - Faster file uploads (no embedding generation during upload)")
        print("  - Reduced costs (embeddings only generated when agent is created)")
        print("  - Improved user experience (immediate file availability)")
    else:
        print("\n💥 Migration failed!")
        print("Please check the error messages above.")
