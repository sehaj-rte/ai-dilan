# Expert Processing Progress Tracking System

## Overview

This system provides real-time progress tracking for expert file processing, allowing users to see the status of their AI expert creation with detailed progress bars and status updates.

## Features

✅ **Real-time Progress Updates** - Track file processing in real-time with detailed progress information
✅ **Database-backed Progress** - All progress stored in PostgreSQL for reliability
✅ **Detailed Stage Tracking** - Track progress through multiple stages: file processing, text extraction, embedding, Pinecone storage
✅ **Batch-level Progress** - See progress at batch and chunk level during embedding generation
✅ **Frontend Integration** - Beautiful progress bars on the dashboard with auto-refresh
✅ **Disabled Chat Until Complete** - Prevents users from chatting with experts until processing is complete
✅ **Error Handling** - Comprehensive error tracking and display

## Architecture

### Backend Components

1. **Database Model** (`models/expert_processing_progress.py`)
   - Stores progress information for each expert
   - Tracks stage, status, file progress, batch progress, chunk progress
   - Includes timing information and error messages

2. **Progress Service** (`services/expert_processing_progress_service.py`)
   - CRUD operations for progress records
   - Helper methods for updating progress
   - Methods to mark completion or failure

3. **Knowledge Base Controller** (`controllers/knowledge_base_controller.py`)
   - Integrated progress tracking during file processing
   - Updates progress at each stage of processing
   - Callback mechanism for embedding progress

4. **Embedding Service** (`services/embedding_service.py`)
   - Support for progress callbacks during batch processing
   - Reports progress after each batch completion

5. **API Routes** (`routes/expert_progress.py`)
   - GET `/api/experts/{expert_id}/progress` - Get progress for specific expert
   - GET `/api/experts/progress/active` - Get all active progress records
   - DELETE `/api/experts/{expert_id}/progress` - Delete progress record

### Frontend Components

1. **Dashboard Page** (`app/dashboard/page.tsx`)
   - Displays progress bars for experts being processed
   - Auto-refreshes progress every 2 seconds
   - Disables chat button until processing complete
   - Shows detailed progress information (stage, percentage, batch/chunk info)

## Progress Stages

The system tracks progress through the following stages:

1. **file_processing** - Initial stage when starting to process files
2. **text_extraction** - Extracting text from uploaded files
3. **embedding** - Generating embeddings (most time-consuming stage)
4. **pinecone_storage** - Storing vectors in Pinecone
5. **complete** - All processing finished successfully
6. **failed** - Processing failed with error

## Progress Information

For each expert being processed, the system tracks:

- **Current Stage** - Which processing stage is active
- **Status** - pending, in_progress, completed, failed
- **File Progress** - Current file index and total files
- **Batch Progress** - Current batch and total batches (during embedding)
- **Chunk Progress** - Current chunk and total chunks (during embedding)
- **Overall Progress** - Percentage completion (0-100%)
- **Timing** - Started, updated, and completed timestamps
- **Error Messages** - If processing fails

## Setup Instructions

### 1. Run Database Migration

```bash
cd /home/kartar/CascadeProjects/dilan-ai-backend
python add_progress_table.py
```

This will create the `expert_processing_progress` table in your database.

### 2. Restart Backend Server

```bash
python main.py
```

The server will automatically import the new model and routes.

### 3. Test the System

1. **Create an Expert with Files**:
   - Go to the dashboard
   - Click "Create Expert"
   - Upload files and create the expert
   - You'll be redirected to the dashboard

2. **Watch Progress**:
   - The expert card will show a progress bar
   - Progress updates automatically every 2 seconds
   - See detailed stage information and percentage

3. **Wait for Completion**:
   - Chat button is disabled during processing
   - Once complete, the progress bar disappears
   - Chat button becomes enabled

## API Usage Examples

### Get Progress for an Expert

```bash
curl http://localhost:8000/api/experts/{expert_id}/progress
```

Response:
```json
{
  "success": true,
  "progress": {
    "id": "uuid",
    "expert_id": "expert-uuid",
    "agent_id": "agent_xxx",
    "stage": "embedding",
    "status": "in_progress",
    "current_file": "document.pdf",
    "current_file_index": 0,
    "total_files": 1,
    "current_batch": 45,
    "total_batches": 100,
    "current_chunk": 450,
    "total_chunks": 1000,
    "processed_files": 0,
    "failed_files": 0,
    "progress_percentage": 45.0,
    "details": {
      "filename": "document.pdf",
      "batch": "45/100",
      "chunks": "450/1000"
    },
    "error_message": null,
    "started_at": "2025-10-10T13:00:00Z",
    "updated_at": "2025-10-10T13:02:30Z",
    "completed_at": null
  }
}
```

### Get All Active Progress Records

```bash
curl http://localhost:8000/api/experts/progress/active
```

Response:
```json
{
  "success": true,
  "count": 2,
  "progress_records": [
    { /* progress record 1 */ },
    { /* progress record 2 */ }
  ]
}
```

### Delete Progress Record (Cleanup)

```bash
curl -X DELETE http://localhost:8000/api/experts/{expert_id}/progress
```

## Console Output Example

During processing, you'll see detailed console output:

```
🚀 Starting Pinecone processing for expert d9941cbb-5ba1-4bbf-b939-1d584574b314 with 1 files
📄 Processing file abc123 for expert d9941cbb-5ba1-4bbf-b939-1d584574b314
📥 Downloading file from S3: expert-files/document.pdf
✅ Successfully downloaded from S3
📝 Extracting text from document.pdf
✅ Extracted 50000 characters from document.pdf
🧠 Embedding Service: Processing document document.pdf
🔄 Processing batch 1/100 (chunks 1-10)
✅ Batch 1 completed: 10/10 chunks embedded
📊 Progress: 10/1000 chunks (1.0%) - Est. 130.0s remaining
...
🎉 Embedding Service: Successfully processed 1000/1000 chunks
🔥 Pinecone Service: Storing document chunks
✅ Successfully stored 1000 chunks
🎉 Pinecone processing complete for expert d9941cbb-5ba1-4bbf-b939-1d584574b314
```

## Frontend Display

The dashboard shows:

1. **Progress Bar** - Animated gradient progress bar (blue to purple)
2. **Stage Label** - Current processing stage in human-readable format
3. **Percentage** - Exact progress percentage
4. **Detailed Info** - File, batch, and chunk information during embedding
5. **Filename** - Current file being processed
6. **Error Messages** - If processing fails
7. **Disabled Chat** - Chat button disabled until complete

## Performance Considerations

- **Polling Interval**: Frontend polls every 2 seconds (configurable)
- **Database Updates**: Progress updated after each batch (not each chunk) to reduce DB load
- **Automatic Cleanup**: Consider adding a cleanup job to remove old completed progress records
- **Batch Size**: Embedding batch size is 10 chunks per API call for optimal performance

## Troubleshooting

### Progress Not Showing

1. Check if progress table exists: `python add_progress_table.py`
2. Verify backend is running and routes are loaded
3. Check browser console for API errors
4. Verify expert ID matches between frontend and backend

### Progress Stuck

1. Check backend console for errors
2. Verify OpenAI API key is valid
3. Check Pinecone connection
4. Look for error messages in progress record

### Chat Button Still Disabled

1. Check if progress status is "completed"
2. Verify progress record exists for expert
3. Try refreshing the dashboard
4. Check if processing actually completed (look at backend logs)

## Future Enhancements

- [ ] WebSocket support for real-time updates (instead of polling)
- [ ] Progress notifications/toasts
- [ ] Estimated time remaining
- [ ] Pause/resume functionality
- [ ] Retry failed files
- [ ] Progress history/logs
- [ ] Email notifications on completion
- [ ] Progress analytics and statistics

## Code Examples

### Updating Progress in Custom Code

```python
from services.expert_processing_progress_service import ExpertProcessingProgressService

# Create progress record
progress_service = ExpertProcessingProgressService(db)
progress_record = progress_service.create_progress_record(
    expert_id="expert-123",
    agent_id="agent-456",
    total_files=5
)

# Update progress
progress_service.update_progress(
    expert_id="expert-123",
    stage="embedding",
    current_batch=10,
    total_batches=50,
    progress_percentage=20.0
)

# Mark as completed
progress_service.mark_completed(
    expert_id="expert-123",
    metadata={"total_time": 120.5}
)

# Mark as failed
progress_service.mark_failed(
    expert_id="expert-123",
    error_message="OpenAI API error"
)
```

## Summary

This progress tracking system provides a complete solution for monitoring expert file processing with:
- Real-time updates
- Detailed progress information
- Beautiful UI with progress bars
- Automatic chat disabling during processing
- Comprehensive error handling
- Easy-to-use API

The system enhances user experience by providing transparency and feedback during the potentially long file processing operations.
