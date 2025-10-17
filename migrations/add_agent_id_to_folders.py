#!/usr/bin/env python3
"""
Migration script to add agent_id column to folders table for agent-specific knowledge base isolation.

This migration:
1. Adds agent_id column to folders table
2. Adds agent_id column to files table (if not exists)
3. Updates existing data to maintain compatibility
4. Creates indexes for performance

Run this script after updating the models to ensure database schema matches.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, Column, String, ForeignKey
from sqlalchemy.orm import sessionmaker
from config.database import DATABASE_URL, Base
from models.folder_db import FolderDB
from models.file_db import FileDB
from models.expert_db import ExpertDB
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the agent_id migration"""
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        logger.info("🚀 Starting agent_id migration for knowledge base isolation...")
        
        # Check if agent_id column exists in folders table
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'folders' AND column_name = 'agent_id'
        """))
        
        if not result.fetchone():
            logger.info("📝 Adding agent_id column to folders table...")
            session.execute(text("""
                ALTER TABLE folders 
                ADD COLUMN agent_id VARCHAR REFERENCES experts(id)
            """))
            session.commit()
            logger.info("✅ Added agent_id column to folders table")
        else:
            logger.info("ℹ️  agent_id column already exists in folders table")
        
        # Check if agent_id column exists in files table
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'files' AND column_name = 'agent_id'
        """))
        
        if not result.fetchone():
            logger.info("📝 Adding agent_id column to files table...")
            session.execute(text("""
                ALTER TABLE files 
                ADD COLUMN agent_id VARCHAR REFERENCES experts(id)
            """))
            session.commit()
            logger.info("✅ Added agent_id column to files table")
        else:
            logger.info("ℹ️  agent_id column already exists in files table")
        
        # Migrate existing data: copy project_id to agent_id for files
        logger.info("📋 Migrating existing file data...")
        result = session.execute(text("""
            UPDATE files 
            SET agent_id = project_id 
            WHERE project_id IS NOT NULL AND agent_id IS NULL
        """))
        migrated_files = result.rowcount
        session.commit()
        logger.info(f"✅ Migrated {migrated_files} files to use agent_id")
        
        # Create indexes for performance
        logger.info("🔍 Creating indexes for performance...")
        
        try:
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_folders_agent_id ON folders(agent_id)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_files_agent_id ON files(agent_id)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_files_agent_folder ON files(agent_id, folder_id)"))
            session.commit()
            logger.info("✅ Created performance indexes")
        except Exception as e:
            logger.warning(f"⚠️  Index creation warning (may already exist): {e}")
        
        # Verify migration
        logger.info("🔍 Verifying migration...")
        
        # Count folders and files by agent
        result = session.execute(text("""
            SELECT 
                COUNT(*) as total_folders,
                COUNT(CASE WHEN agent_id IS NOT NULL THEN 1 END) as agent_folders
            FROM folders
        """))
        folder_stats = result.fetchone()
        
        result = session.execute(text("""
            SELECT 
                COUNT(*) as total_files,
                COUNT(CASE WHEN agent_id IS NOT NULL THEN 1 END) as agent_files,
                COUNT(CASE WHEN project_id IS NOT NULL THEN 1 END) as project_files
            FROM files
        """))
        file_stats = result.fetchone()
        
        logger.info(f"📊 Migration Summary:")
        logger.info(f"   Folders: {folder_stats[0]} total, {folder_stats[1]} with agent_id")
        logger.info(f"   Files: {file_stats[0]} total, {file_stats[1]} with agent_id, {file_stats[2]} with project_id")
        
        session.close()
        logger.info("🎉 Agent isolation migration completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

def rollback_migration():
    """Rollback the migration (remove agent_id columns)"""
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        logger.info("🔄 Rolling back agent_id migration...")
        
        # Remove indexes
        session.execute(text("DROP INDEX IF EXISTS idx_folders_agent_id"))
        session.execute(text("DROP INDEX IF EXISTS idx_files_agent_id"))
        session.execute(text("DROP INDEX IF EXISTS idx_files_agent_folder"))
        
        # Remove columns (be careful - this will lose data!)
        logger.warning("⚠️  This will remove agent_id columns and lose isolation data!")
        confirm = input("Are you sure you want to continue? (yes/no): ")
        
        if confirm.lower() == 'yes':
            session.execute(text("ALTER TABLE folders DROP COLUMN IF EXISTS agent_id"))
            session.execute(text("ALTER TABLE files DROP COLUMN IF EXISTS agent_id"))
            session.commit()
            logger.info("✅ Rollback completed")
        else:
            logger.info("❌ Rollback cancelled")
        
        session.close()
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent isolation migration for knowledge base")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        success = run_migration()
        if not success:
            sys.exit(1)
