#!/usr/bin/env python3
"""
Migration script to remove foreign key constraint from agent_id column in files table.

This migration:
1. Removes the foreign key constraint from agent_id column in files table
2. Removes the foreign key constraint from agent_id column in folders table
3. Allows storing ElevenLabs agent IDs (like "agent_bdrk_...") in these columns

Run this script to fix the issue where agent_id and project_id are being stored as NULL
because of foreign key constraint violations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.database import DATABASE_URL
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the agent_id constraint removal migration"""
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        logger.info("🚀 Starting agent_id constraint removal migration...")
        
        # Check if foreign key constraint exists on files.agent_id
        result = session.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'files' 
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%agent_id%'
        """))
        
        fk_constraints = result.fetchall()
        
        for constraint in fk_constraints:
            constraint_name = constraint[0]
            logger.info(f"📝 Removing foreign key constraint '{constraint_name}' from files table...")
            session.execute(text(f"ALTER TABLE files DROP CONSTRAINT {constraint_name}"))
            session.commit()
            logger.info(f"✅ Removed foreign key constraint '{constraint_name}' from files table")
        
        if not fk_constraints:
            logger.info("ℹ️  No foreign key constraints found on files.agent_id column")
        
        # Check if foreign key constraint exists on folders.agent_id
        result = session.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'folders' 
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%agent_id%'
        """))
        
        fk_constraints = result.fetchall()
        
        for constraint in fk_constraints:
            constraint_name = constraint[0]
            logger.info(f"📝 Removing foreign key constraint '{constraint_name}' from folders table...")
            session.execute(text(f"ALTER TABLE folders DROP CONSTRAINT {constraint_name}"))
            session.commit()
            logger.info(f"✅ Removed foreign key constraint '{constraint_name}' from folders table")
        
        if not fk_constraints:
            logger.info("ℹ️  No foreign key constraints found on folders.agent_id column")
        
        session.close()
        logger.info("🎉 Agent_id constraint removal migration completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

def rollback_migration():
    """Rollback the migration (re-add foreign key constraints)"""
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        logger.info("🔄 Rolling back agent_id constraint removal migration...")
        
        # Note: We can't easily recreate the exact constraint without knowing its name
        # This would require manual intervention or more complex logic
        logger.warning("⚠️  Rollback not implemented - foreign key constraints would need to be manually recreated")
        
        session.close()
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove foreign key constraints from agent_id columns")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        success = run_migration()
        if not success:
            sys.exit(1)
