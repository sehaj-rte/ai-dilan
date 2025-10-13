#!/usr/bin/env python3
"""
Database Migration Script - Add Missing Columns
This script adds missing columns to existing tables in the Dilan AI database.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get database connection"""
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "dilan_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "")
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        );
    """, (table_name, column_name))
    return cursor.fetchone()[0]

def table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = %s
        );
    """, (table_name,))
    return cursor.fetchone()[0]

def add_missing_expert_columns(cursor):
    """Add missing columns to experts table"""
    print("Checking experts table...")
    
    if not table_exists(cursor, 'experts'):
        print("Creating experts table...")
        cursor.execute("""
            CREATE TABLE experts (
                id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                system_prompt TEXT,
                voice_id VARCHAR(255),
                elevenlabs_agent_id VARCHAR(255) UNIQUE,
                avatar_url VARCHAR(500),
                pinecone_index_name VARCHAR(255),
                selected_files JSON,
                knowledge_base_tool_id VARCHAR(255),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✓ Created experts table")
        return
    
    # Add missing columns to existing experts table
    columns_to_add = [
        ("description", "TEXT"),
        ("system_prompt", "TEXT"),
        ("voice_id", "VARCHAR(255)"),
        ("elevenlabs_agent_id", "VARCHAR(255)"),
        ("avatar_url", "VARCHAR(500)"),
        ("pinecone_index_name", "VARCHAR(255)"),
        ("selected_files", "JSON"),
        ("knowledge_base_tool_id", "VARCHAR(255)"),
        ("is_active", "BOOLEAN DEFAULT true"),
        ("created_at", "TIMESTAMP WITH TIME ZONE DEFAULT NOW()"),
        ("updated_at", "TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
    ]
    
    for column_name, column_type in columns_to_add:
        if not column_exists(cursor, 'experts', column_name):
            try:
                cursor.execute(f"ALTER TABLE experts ADD COLUMN {column_name} {column_type};")
                print(f"✓ Added column: experts.{column_name}")
            except Exception as e:
                print(f"✗ Error adding column experts.{column_name}: {e}")
        else:
            print(f"- Column experts.{column_name} already exists")
    
    # Add unique constraint for elevenlabs_agent_id if it doesn't exist
    try:
        cursor.execute("""
            SELECT constraint_name FROM information_schema.table_constraints 
            WHERE table_name = 'experts' AND constraint_type = 'UNIQUE' 
            AND constraint_name LIKE '%elevenlabs_agent_id%';
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE experts ADD CONSTRAINT experts_elevenlabs_agent_id_key UNIQUE (elevenlabs_agent_id);")
            print("✓ Added unique constraint for elevenlabs_agent_id")
    except Exception as e:
        print(f"Note: Could not add unique constraint for elevenlabs_agent_id: {e}")

def add_missing_file_columns(cursor):
    """Add missing columns to files table"""
    print("\nChecking files table...")
    
    if not table_exists(cursor, 'files'):
        print("Creating files table...")
        cursor.execute("""
            CREATE TABLE files (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                original_name VARCHAR(255) NOT NULL,
                size INTEGER NOT NULL,
                type VARCHAR(100) NOT NULL,
                s3_url TEXT NOT NULL,
                s3_key VARCHAR(500) NOT NULL,
                user_id UUID,
                description TEXT,
                tags JSON,
                document_type VARCHAR(50),
                language VARCHAR(10),
                word_count INTEGER,
                page_count INTEGER,
                processing_status VARCHAR(20) DEFAULT 'pending',
                processing_error TEXT,
                extracted_text_preview TEXT,
                has_images BOOLEAN DEFAULT false,
                has_tables BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("✓ Created files table")
        return
    
    # Add missing columns to existing files table
    columns_to_add = [
        ("original_name", "VARCHAR(255)"),
        ("user_id", "UUID"),
        ("description", "TEXT"),
        ("tags", "JSON"),
        ("document_type", "VARCHAR(50)"),
        ("language", "VARCHAR(10)"),
        ("word_count", "INTEGER"),
        ("page_count", "INTEGER"),
        ("processing_status", "VARCHAR(20) DEFAULT 'pending'"),
        ("processing_error", "TEXT"),
        ("extracted_text_preview", "TEXT"),
        ("has_images", "BOOLEAN DEFAULT false"),
        ("has_tables", "BOOLEAN DEFAULT false"),
        ("created_at", "TIMESTAMP DEFAULT NOW()"),
        ("updated_at", "TIMESTAMP DEFAULT NOW()")
    ]
    
    for column_name, column_type in columns_to_add:
        if not column_exists(cursor, 'files', column_name):
            try:
                cursor.execute(f"ALTER TABLE files ADD COLUMN {column_name} {column_type};")
                print(f"✓ Added column: files.{column_name}")
            except Exception as e:
                print(f"✗ Error adding column files.{column_name}: {e}")
        else:
            print(f"- Column files.{column_name} already exists")

def create_missing_tables(cursor):
    """Create any missing tables"""
    print("\nChecking for missing tables...")
    
    # Check if users table exists (from previous memory)
    if not table_exists(cursor, 'users'):
        print("Creating users table...")
        cursor.execute("""
            CREATE TABLE users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR UNIQUE NOT NULL,
                username VARCHAR UNIQUE NOT NULL,
                full_name VARCHAR,
                hashed_password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_users_email ON users(email);")
        cursor.execute("CREATE INDEX idx_users_username ON users(username);")
        print("✓ Created users table with indexes")
    else:
        print("- Users table already exists")

def update_existing_data(cursor):
    """Update existing data to set default values"""
    print("\nUpdating existing data...")
    
    # Set default values for experts
    try:
        cursor.execute("UPDATE experts SET is_active = true WHERE is_active IS NULL;")
        cursor.execute("UPDATE experts SET created_at = NOW() WHERE created_at IS NULL;")
        cursor.execute("UPDATE experts SET updated_at = NOW() WHERE updated_at IS NULL;")
        print("✓ Updated experts default values")
    except Exception as e:
        print(f"Note: Could not update experts defaults: {e}")
    
    # Set default values for files
    try:
        cursor.execute("UPDATE files SET processing_status = 'pending' WHERE processing_status IS NULL;")
        cursor.execute("UPDATE files SET has_images = false WHERE has_images IS NULL;")
        cursor.execute("UPDATE files SET has_tables = false WHERE has_tables IS NULL;")
        cursor.execute("UPDATE files SET created_at = NOW() WHERE created_at IS NULL;")
        cursor.execute("UPDATE files SET updated_at = NOW() WHERE updated_at IS NULL;")
        cursor.execute("UPDATE files SET original_name = name WHERE original_name IS NULL;")
        print("✓ Updated files default values")
    except Exception as e:
        print(f"Note: Could not update files defaults: {e}")

def main():
    """Main migration function"""
    print("🚀 Starting database migration...")
    print("=" * 50)
    
    # Connect to database
    connection = get_db_connection()
    if not connection:
        print("❌ Failed to connect to database")
        sys.exit(1)
    
    try:
        cursor = connection.cursor()
        
        # Create missing tables
        create_missing_tables(cursor)
        
        # Add missing columns
        add_missing_expert_columns(cursor)
        add_missing_file_columns(cursor)
        
        # Update existing data
        update_existing_data(cursor)
        
        print("\n" + "=" * 50)
        print("✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart your FastAPI server")
        print("2. Test the /experts/ and /knowledge-base/files endpoints")
        print("3. Check that all functionality works as expected")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    main()
