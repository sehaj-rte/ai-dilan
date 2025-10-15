# Custom Knowledge Base Setup Guide

This guide explains how to set up and use the custom knowledge base system that allows your AI experts to search through your uploaded documents.

## 🎯 Overview

The custom knowledge base system enables:
- **Document Upload & Processing**: Extract text from PDFs, DOCX, images, audio, etc.
- **Intelligent Chunking**: Split documents into searchable chunks with embeddings
- **User Isolation**: Each user has their own knowledge base namespace
- **AI Integration**: ElevenLabs agents automatically search your documents during conversations
- **Real-time Updates**: New uploads are immediately available to AI experts

## 🔧 Setup Requirements

### 1. Environment Variables

Add these to your `.env` file:

```bash
# Pinecone Configuration (for vector storage)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_USER_KB_INDEX=user-knowledge-base

# OpenAI Configuration (for embeddings)
OPENAI_API_KEY=your_openai_api_key_here

# Webhook Configuration (for AI agent integration)
BASE_URL=http://localhost:8000
WEBHOOK_AUTH_TOKEN=your-secret-webhook-token

# AWS S3 Configuration (for file storage)
S3_BUCKET_NAME=your_s3_bucket_name
S3_ACCESS_KEY_ID=your_s3_access_key_id
S3_SECRET_KEY=your_s3_secret_key
S3_REGION=us-west-2
```

### 2. Pinecone Index Setup

Create a Pinecone index for the knowledge base:

```python
# Index Configuration
Index Name: user-knowledge-base
Dimensions: 3072 (for text-embedding-3-large)
Metric: cosine
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

The system includes these new dependencies:
- `PyPDF2==3.0.1` - PDF text extraction
- `python-docx==1.1.0` - DOCX text extraction
- `Pillow==10.1.0` - Image processing
- `pytesseract==0.3.10` - OCR for images
- `SpeechRecognition==3.10.0` - Audio transcription
- `pydub==0.25.1` - Audio processing

### 4. System Dependencies (Optional)

For full functionality, install:
- **Tesseract OCR**: For extracting text from images
  ```bash
  # Ubuntu/Debian
  sudo apt-get install tesseract-ocr
  
  # macOS
  brew install tesseract
  ```

## 🚀 How It Works

### 1. File Upload Process

```
User uploads file → Validate → Store in S3 → Extract text → 
Create chunks → Generate embeddings → Store in Pinecone → 
Save metadata in PostgreSQL
```

### 2. Expert Creation Process

```
Create expert → Create ElevenLabs agent → 
Attach knowledge base tool → Save to database
```

### 3. Conversation Process

```
User asks question → AI agent processes → 
Determines need for knowledge → Calls search webhook → 
Search user's Pinecone namespace → Return relevant chunks → 
AI incorporates knowledge → Enhanced response
```

## 📋 API Endpoints

### Knowledge Base Management

```bash
# Upload file to knowledge base
POST /knowledge-base/upload
Content-Type: multipart/form-data
Body: file (PDF, DOCX, TXT, CSV, images, audio, video)

# List uploaded files
GET /knowledge-base/files

# Get specific file
GET /knowledge-base/files/{file_id}

# Delete file (removes from S3, database, and Pinecone)
DELETE /knowledge-base/files/{file_id}

# Get usage statistics
GET /knowledge-base/stats
```

### Search Integration

```bash
# Search user's knowledge base (used by AI agents)
POST /tools/search-user-knowledge?user_id={user_id}
Body: {"query": "search terms"}

# Health check
GET /tools/pinecone-search/health
```

## 🎯 Supported File Types

| Type | Extensions | Processing Method |
|------|------------|-------------------|
| **Documents** | PDF, DOCX, TXT, CSV | Text extraction |
| **Images** | JPG, PNG, GIF | OCR (Tesseract) |
| **Audio** | MP3, WAV | Speech recognition |
| **Video** | MP4, AVI | Planned (not implemented) |

## 🔍 Usage Examples

### 1. Upload a Document

```bash
curl -X POST "http://localhost:8000/knowledge-base/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@research_paper.pdf"
```

### 2. Create Expert with Knowledge Base

```python
expert_data = {
    "name": "Research Assistant",
    "description": "AI expert with access to uploaded research papers",
    "system_prompt": "You are a research assistant with access to uploaded documents...",
    "voice_id": "elevenlabs_voice_id",
    "user_id": "user_123"  # Important for knowledge base isolation
}

result = await create_expert_with_elevenlabs(db, expert_data)
```

### 3. Chat with Knowledge-Enhanced Expert

The AI expert will automatically search your uploaded documents when relevant:

```
User: "What does the research say about machine learning trends?"
AI: *searches uploaded research papers*
AI: "Based on your uploaded research paper 'ML_Trends_2024.pdf', 
     the key trends include..."
```

## 🛡️ Security & Privacy

### User Isolation
- Each user has a separate Pinecone namespace: `user_{user_id}`
- Users can only access their own uploaded documents
- AI experts only search the creator's knowledge base

### Data Protection
- Files stored securely in AWS S3
- Metadata encrypted in PostgreSQL
- Webhook authentication with bearer tokens
- No cross-user data leakage

## 🔧 Troubleshooting

### Common Issues

1. **Text extraction fails**
   - Check file format is supported
   - Ensure file is not corrupted
   - For images: Install Tesseract OCR

2. **Embedding generation fails**
   - Verify OpenAI API key is valid
   - Check API quota and billing
   - Ensure text content is not empty

3. **Pinecone storage fails**
   - Verify Pinecone API key and index name
   - Check index dimensions match (3072)
   - Ensure sufficient Pinecone quota

4. **AI agent doesn't use knowledge base**
   - Verify webhook URL is accessible
   - Check webhook authentication token
   - Ensure tool was attached during expert creation

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 📊 Monitoring

### File Processing Status

Each upload returns processing status:

```json
{
  "success": true,
  "id": "file_uuid",
  "processing": {
    "text_extraction": {"word_count": 1500},
    "document_processing": {"total_chunks": 3},
    "knowledge_base_storage": {"chunks_stored": 3}
  }
}
```

### Search Analytics

Monitor search performance:
- Query response times
- Relevance scores
- User engagement with results

## 🚀 Next Steps

1. **Test the system** with sample documents
2. **Configure authentication** for user isolation
3. **Set up monitoring** for production use
4. **Customize chunking** parameters for your use case
5. **Add more file types** as needed

## 💡 Tips for Best Results

1. **Upload relevant documents**: The AI can only use what you upload
2. **Use descriptive filenames**: Helps with search context
3. **Organize by topic**: Consider separate experts for different domains
4. **Monitor storage usage**: Keep track of Pinecone and S3 costs
5. **Regular cleanup**: Remove outdated documents

Your AI experts now have access to your custom knowledge base and will provide more accurate, contextual responses based on your uploaded documents!
