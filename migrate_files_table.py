"""
Migration script to add missing columns to the files table.
This adds all the enhanced metadata and content fields.

Run this script once to update your production database:
python migrate_files_table.py
"""

import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in environment variables")
    exit(1)

print(f"🔗 Connecting to database...")
engine = create_engine(DATABASE_URL)

# List of columns to add with their SQL definitions
columns_to_add = [
    ("content", "BYTEA"),  # For storing file content as fallback
    ("description", "TEXT"),
    ("tags", "JSON"),
    ("document_type", "VARCHAR(50)"),
    ("language", "VARCHAR(10)"),
    ("word_count", "INTEGER"),
    ("page_count", "INTEGER"),
    ("processing_status", "VARCHAR(20) DEFAULT 'pending'"),
    ("processing_error", "TEXT"),
    ("extracted_text", "TEXT"),
    ("extracted_text_preview", "TEXT"),
    ("has_images", "BOOLEAN DEFAULT FALSE"),
    ("has_tables", "BOOLEAN DEFAULT FALSE"),
]

def column_exists(inspector, table_name, column_name):
    """Check if a column exists in a table"""
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def main():
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # Check if files table exists
            if 'files' not in inspector.get_table_names():
                print("❌ ERROR: 'files' table does not exist")
                return
            
            print("✅ Found 'files' table")
            print("\n📋 Checking for missing columns...\n")
            
            columns_added = 0
            columns_skipped = 0
            
            for column_name, column_type in columns_to_add:
                if column_exists(inspector, 'files', column_name):
                    print(f"⏭️  Column '{column_name}' already exists - skipping")
                    columns_skipped += 1
                else:
                    try:
                        # Add the column
                        sql = text(f"ALTER TABLE files ADD COLUMN {column_name} {column_type}")
                        conn.execute(sql)
                        conn.commit()
                        print(f"✅ Added column '{column_name}' ({column_type})")
                        columns_added += 1
                    except Exception as e:
                        print(f"❌ Error adding column '{column_name}': {e}")
            
            print(f"\n{'='*60}")
            print(f"📊 Migration Summary:")
            print(f"   ✅ Columns added: {columns_added}")
            print(f"   ⏭️  Columns skipped (already exist): {columns_skipped}")
            print(f"{'='*60}\n")
            
            if columns_added > 0:
                print("🎉 Migration completed successfully!")
            else:
                print("ℹ️  No changes needed - all columns already exist")
                
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()
