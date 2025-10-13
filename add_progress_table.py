"""
Migration script to add expert_processing_progress table
Run this script to create the new table in your database
"""

from config.database import engine, Base
from models.expert_processing_progress import ExpertProcessingProgress
from sqlalchemy import inspect

def add_progress_table():
    """Add expert_processing_progress table to database"""
    try:
        # Check if table already exists
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if 'expert_processing_progress' in existing_tables:
            print("✅ Table 'expert_processing_progress' already exists")
            return True
        
        print("📊 Creating expert_processing_progress table...")
        
        # Create the table
        ExpertProcessingProgress.__table__.create(engine)
        
        print("✅ Successfully created expert_processing_progress table!")
        print("\nTable structure:")
        print("  - id (UUID, primary key)")
        print("  - expert_id (String, indexed)")
        print("  - agent_id (String)")
        print("  - stage (String)")
        print("  - status (String)")
        print("  - current_file (String, nullable)")
        print("  - current_file_index (Integer)")
        print("  - total_files (Integer)")
        print("  - current_batch (Integer)")
        print("  - total_batches (Integer)")
        print("  - current_chunk (Integer)")
        print("  - total_chunks (Integer)")
        print("  - processed_files (Integer)")
        print("  - failed_files (Integer)")
        print("  - progress_percentage (Float)")
        print("  - details (JSON)")
        print("  - error_message (Text, nullable)")
        print("  - started_at (DateTime)")
        print("  - updated_at (DateTime)")
        print("  - completed_at (DateTime, nullable)")
        print("  - processing_metadata (JSON)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting migration: Add expert_processing_progress table\n")
    success = add_progress_table()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\nYou can now:")
        print("  1. Create experts with file processing")
        print("  2. Track progress in real-time via API")
        print("  3. View progress bars on the dashboard")
    else:
        print("\n❌ Migration failed. Please check the error above.")
