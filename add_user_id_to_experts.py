"""
Migration script to add user_id column to experts table
Run this script once to update the database schema
"""

from sqlalchemy import create_engine, text
from config.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Add user_id column to experts table"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='experts' AND column_name='user_id'
            """))
            
            if result.fetchone():
                logger.info("✅ user_id column already exists in experts table")
                return
            
            # Add user_id column
            logger.info("Adding user_id column to experts table...")
            conn.execute(text("""
                ALTER TABLE experts 
                ADD COLUMN user_id VARCHAR(255) DEFAULT 'default_user' NOT NULL
            """))
            
            # Create index on user_id
            logger.info("Creating index on user_id...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_experts_user_id ON experts(user_id)
            """))
            
            conn.commit()
            
            logger.info("✅ Migration completed successfully!")
            logger.info("   - Added user_id column to experts table")
            logger.info("   - Created index on user_id")
            logger.info("   - Existing experts assigned to 'default_user'")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    logger.info("🚀 Starting migration: Add user_id to experts table")
    migrate()
    logger.info("🎉 Migration complete!")
