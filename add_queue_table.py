"""
Migration script to add processing_queue table and update expert_processing_progress table
Run this script to create/update tables for the queue system
"""

from config.database import engine, Base
from models.processing_queue import ProcessingQueue
from models.expert_processing_progress import ExpertProcessingProgress
from sqlalchemy import inspect, text

def add_queue_tables():
    """Add processing_queue table and update expert_processing_progress"""
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Create processing_queue table
        if 'processing_queue' not in existing_tables:
            print("📊 Creating processing_queue table...")
            ProcessingQueue.__table__.create(engine)
            print("✅ Successfully created processing_queue table!")
        else:
            print("✅ Table 'processing_queue' already exists")
        
        # Update expert_processing_progress table with new columns
        print("\n📊 Updating expert_processing_progress table...")
        
        with engine.connect() as conn:
            # Check if columns exist
            columns = [col['name'] for col in inspector.get_columns('expert_processing_progress')]
            
            if 'queue_position' not in columns:
                print("  Adding queue_position column...")
                conn.execute(text("ALTER TABLE expert_processing_progress ADD COLUMN queue_position INTEGER"))
                conn.commit()
                print("  ✅ Added queue_position column")
            
            if 'task_id' not in columns:
                print("  Adding task_id column...")
                conn.execute(text("ALTER TABLE expert_processing_progress ADD COLUMN task_id VARCHAR"))
                conn.commit()
                print("  ✅ Added task_id column")
        
        print("\n✅ All tables updated successfully!")
        print("\nQueue System Tables:")
        print("  1. processing_queue - Stores queued tasks")
        print("  2. expert_processing_progress - Updated with queue info")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating tables: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting migration: Add queue system tables\n")
    success = add_queue_tables()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\nYou can now:")
        print("  1. Create multiple experts simultaneously")
        print("  2. Tasks will be queued and processed sequentially")
        print("  3. View queue position on dashboard")
        print("  4. Background worker processes tasks automatically")
        print("\n🚀 Restart your server to start the queue worker!")
    else:
        print("\n❌ Migration failed. Please check the error above.")
