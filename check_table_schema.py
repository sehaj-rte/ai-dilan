#!/usr/bin/env python3
"""
Check the actual database table schema to see what columns exist
"""

import os
from sqlalchemy import create_engine, text
from config.database import DATABASE_URL
from dotenv import load_dotenv

def main():
    """Check the experts table schema"""
    
    # Load environment variables
    load_dotenv()
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/dilan_ai_db")
    
    try:
        # Create engine
        engine = create_engine(db_url)
        
        # Check if experts table exists and get its schema
        with engine.connect() as conn:
            print("🔍 Checking experts table schema...")
            
            # Get table columns
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'experts' 
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            
            if columns:
                print("✅ Experts table exists with the following columns:")
                print("-" * 60)
                for col in columns:
                    print(f"Column: {col[0]:<25} Type: {col[1]:<15} Nullable: {col[2]}")
                print("-" * 60)
            else:
                print("❌ Experts table does not exist or has no columns")
                
            # Check if table exists at all
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'experts'
                );
            """))
            
            table_exists = result.fetchone()[0]
            print(f"Table exists: {table_exists}")
            
    except Exception as e:
        print(f"❌ Error checking database schema: {str(e)}")

if __name__ == "__main__":
    main()
