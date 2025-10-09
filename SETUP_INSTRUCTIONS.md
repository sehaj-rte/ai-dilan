# Setup Instructions for Expert Creation System

## Issues Fixed:

### 1. AWS S3 ACL Error
✅ **FIXED**: Removed `ACL='public-read'` from S3 upload since your bucket doesn't support ACLs.

**Note**: Make sure your S3 bucket (`ai-dilan`) has a bucket policy that allows public read access:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::ai-dilan/*"
        }
    ]
}
```

### 2. PostgreSQL Connection Error
❌ **NEEDS CONFIGURATION**: Update your `.env` file with correct database credentials.

## Required .env Configuration:

Update your `/home/kartar/CascadeProjects/dilan-ai-backend/.env` file with:

```bash
# Database Configuration - UPDATE THESE VALUES
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/dilan_ai_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dilan_ai_db
DB_USER=your_username
DB_PASSWORD=your_password

# AWS S3 Configuration - ALREADY CONFIGURED
S3_BUCKET_NAME=ai-dilan
S3_ACCESS_KEY_ID=your_s3_access_key_id
S3_SECRET_KEY=your_s3_secret_key
S3_REGION=us-east-1

# ElevenLabs Configuration - ADD YOUR API KEY
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

## Database Setup Options:

### Option 1: Use SQLite (Easiest for Development)
Update your `.env` file:
```bash
DATABASE_URL=sqlite:///./dilan_ai.db
```

### Option 2: Setup PostgreSQL
1. Install PostgreSQL
2. Create database and user:
```sql
CREATE DATABASE dilan_ai_db;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE dilan_ai_db TO your_username;
```
3. Update `.env` with your credentials

## Test the Fix:

1. Update your `.env` file with correct database credentials
2. Restart your backend server
3. Try creating an expert again

The system should now:
- ✅ Upload images to S3 successfully (without ACL)
- ✅ Save expert data to database
- ✅ Create ElevenLabs agents
- ✅ Return success response

## Current Status:
- **ElevenLabs**: ✅ Working (agent created: `agent_3501k74ch53nekm9cn338zqrs44e`)
- **AWS S3**: ✅ Fixed (ACL issue resolved)
- **Database**: ❌ Needs credential configuration
