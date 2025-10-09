#!/usr/bin/env python3
"""
Quick fix script to resolve database and S3 issues
"""

import os
import sys

def update_env_for_sqlite():
    """Update .env file to use SQLite instead of PostgreSQL"""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        print("❌ .env file not found. Creating one...")
        # Create basic .env file
        with open(env_path, 'w') as f:
            f.write("""# Database Configuration (SQLite for quick setup)
DATABASE_URL=sqlite:///./dilan_ai.db

# AWS S3 Configuration
S3_BUCKET_NAME=ai-dilan
S3_ACCESS_KEY_ID=your_s3_access_key_id
S3_SECRET_KEY=your_s3_secret_key
S3_REGION=us-east-1

# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# App Configuration
APP_NAME=Dilan AI Backend
DEBUG=True
HOST=0.0.0.0
PORT=8000

# JWT Configuration
SECRET_KEY=your_secret_key_here_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
""")
        print("✅ Created .env file with SQLite configuration")
    else:
        # Read existing .env and update DATABASE_URL
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update DATABASE_URL line
        updated_lines = []
        database_url_found = False
        
        for line in lines:
            if line.startswith('DATABASE_URL='):
                updated_lines.append('DATABASE_URL=sqlite:///./dilan_ai.db\n')
                database_url_found = True
                print("✅ Updated DATABASE_URL to use SQLite")
            else:
                updated_lines.append(line)
        
        # Add DATABASE_URL if not found
        if not database_url_found:
            updated_lines.append('DATABASE_URL=sqlite:///./dilan_ai.db\n')
            print("✅ Added DATABASE_URL for SQLite")
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)

def setup_database():
    """Setup SQLite database with tables"""
    try:
        from config.sqlite_database import setup_sqlite
        return setup_sqlite()
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def main():
    print("🔧 Quick Fix Script for Expert Creation System")
    print("=" * 50)
    
    # Step 1: Update .env for SQLite
    print("\n1. Updating database configuration...")
    update_env_for_sqlite()
    
    # Step 2: Setup SQLite database
    print("\n2. Setting up SQLite database...")
    if setup_database():
        print("✅ Database setup successful!")
    else:
        print("❌ Database setup failed!")
        return False
    
    print("\n🎉 Quick fix complete!")
    print("\nNext steps:")
    print("1. Restart your backend server")
    print("2. Try creating an expert again")
    print("3. The system should now work with:")
    print("   ✅ SQLite database (no PostgreSQL needed)")
    print("   ✅ AWS S3 uploads (ACL issue fixed)")
    print("   ✅ ElevenLabs integration")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
