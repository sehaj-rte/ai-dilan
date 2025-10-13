# Production-Ready File Storage Implementation

## Overview
This implementation uses AWS S3 for file storage, keeping the database lean and scalable for production use.

## Architecture

### File Upload Flow
1. **User uploads file** → API receives file content
2. **Upload to S3** → File stored in AWS S3 bucket
3. **Save metadata** → Only metadata (name, size, S3 key, etc.) stored in PostgreSQL
4. **Return success** → User gets confirmation with file ID

### File Processing Flow (Expert Creation)
1. **User creates expert** → Selects files to include
2. **Download from S3** → System downloads file content from S3 using S3 key
3. **Extract text** → Document processor extracts text from file
4. **Generate embeddings** → Embedding service chunks text and creates embeddings
5. **Store in Pinecone** → Embeddings stored in Pinecone for semantic search
6. **Complete** → Expert can now search the knowledge base

## Key Components

### 1. AWS S3 Service (`services/aws_s3_service.py`)
- **`upload_file()`** - Uploads file content to S3
- **`download_file()`** - Downloads file content from S3 using S3 key
- **`delete_image()`** - Deletes files from S3

### 2. File Service (`services/file_service.py`)
- Uploads files to S3
- Stores only metadata in database (NO file content)
- Provides file retrieval methods

### 3. Knowledge Base Controller (`controllers/knowledge_base_controller.py`)
- Downloads files from S3 when needed for processing
- Processes files into Pinecone during expert creation
- Handles errors gracefully with fallbacks

## Benefits

### ✅ Scalability
- Database stays small (only metadata)
- S3 handles large files efficiently
- Can store unlimited files

### ✅ Performance
- Fast database queries (no large binary data)
- S3 provides fast file downloads
- Parallel processing possible

### ✅ Cost-Effective
- S3 storage is cheaper than database storage
- Pay only for what you use
- Automatic scaling

### ✅ Reliability
- S3 provides 99.999999999% durability
- Automatic backups and versioning
- Geographic redundancy

## Configuration

### Required Environment Variables
```env
# AWS S3 Configuration
S3_BUCKET_NAME=your-bucket-name
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_KEY=your-secret-key
S3_REGION=us-east-1
```

### AWS S3 Setup
1. Create an S3 bucket in AWS Console
2. Configure bucket permissions (allow your app to read/write)
3. Create IAM user with S3 access
4. Add credentials to `.env` file

## Fallback Behavior

If S3 is not configured or fails:
- System logs warning
- Creates temporary URL placeholder
- File processing will fail gracefully with clear error messages
- System remains operational for other features

## Database Schema

```sql
CREATE TABLE files (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    size INTEGER NOT NULL,
    type VARCHAR(100) NOT NULL,
    s3_url TEXT NOT NULL,           -- Public URL to access file
    s3_key VARCHAR(500) NOT NULL,   -- S3 key for downloading
    user_id UUID,
    -- Metadata fields (no content column)
    document_type VARCHAR(50),
    language VARCHAR(10),
    word_count INTEGER,
    page_count INTEGER,
    processing_status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Console Logging

The system provides detailed console logging for debugging:
- 📥 Downloading file from S3
- ✅ Successfully downloaded file from S3
- 📝 Extracting text from file
- 🧠 Generating embeddings
- 🔥 Storing in Pinecone
- ✅ Successfully processed file

## Error Handling

### S3 Download Failures
- Logs error with S3 key
- Returns clear error message
- Continues processing other files
- Reports failed files in summary

### Missing S3 Configuration
- Falls back to temporary URLs
- Logs warning messages
- System remains functional
- Clear error messages for users

## Testing

Test the S3 integration:
```bash
# 1. Upload a file
curl -X POST http://localhost:8000/knowledge-base/upload \
  -F "file=@test.pdf"

# 2. Create expert with file
curl -X POST http://localhost:8000/experts/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Expert",
    "system_prompt": "You are a helpful assistant",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "selected_files": ["file-id-here"]
  }'

# 3. Check logs for S3 download activity
```

## Migration from Database Storage

If you previously stored content in database:
1. Files already in database will continue to work
2. New uploads will use S3
3. Optionally migrate old files to S3
4. Remove content column when ready

## Production Checklist

- [ ] AWS S3 bucket created
- [ ] IAM user with S3 permissions created
- [ ] Environment variables configured
- [ ] S3 bucket CORS configured (if needed for direct uploads)
- [ ] Bucket lifecycle policies configured (optional)
- [ ] Monitoring and alerts set up
- [ ] Backup strategy defined
- [ ] Cost monitoring enabled

## Support

For issues or questions:
1. Check S3 credentials in `.env`
2. Verify S3 bucket permissions
3. Check console logs for detailed error messages
4. Ensure network connectivity to AWS
