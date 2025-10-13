# Queue System for Expert File Processing

## Overview

Implemented a database-backed queue system (without Redis) that allows multiple users to create experts simultaneously. Tasks are queued and processed sequentially by a background worker.

## Architecture

### Components

1. **Processing Queue Table** (`models/processing_queue.py`)
   - Stores all queued tasks
   - Tracks task status, priority, queue position
   - Handles retries and error tracking

2. **Queue Service** (`services/queue_service.py`)
   - Manages queue operations (enqueue, dequeue, update status)
   - Updates queue positions automatically
   - Provides queue statistics

3. **Queue Worker** (`services/queue_worker.py`)
   - Background worker that processes tasks
   - Polls queue every 2 seconds
   - Processes one task at a time
   - Handles retries and failures

4. **Progress Tracking** (Updated)
   - Added `queue_position` and `task_id` fields
   - Shows "Queued (Position X)" status
   - Syncs with queue automatically

## How It Works

### 1. Expert Creation Flow

```
User Creates Expert with Files
  ↓
Expert & Agent Created
  ↓
Progress Record Created (status: "queued")
  ↓
Task Added to Queue
  ↓
Return Success to User Immediately
  ↓
User Sees "Queued (Position X)" on Dashboard
```

### 2. Background Processing

```
Queue Worker (Running in Background)
  ↓
Poll Queue Every 2 Seconds
  ↓
Get Next Task (Highest Priority, Oldest First)
  ↓
Mark Task as "Processing"
  ↓
Process Files (Extract → Embed → Store in Pinecone)
  ↓
Update Progress in Real-time
  ↓
Mark Task as "Completed" or "Failed"
  ↓
Repeat
```

### 3. Multiple Users Scenario

```
User A creates Expert 1 → Task 1 (Position 1) → Processing
User B creates Expert 2 → Task 2 (Position 2) → Queued
User C creates Expert 3 → Task 3 (Position 3) → Queued

Task 1 completes → Task 2 moves to Position 1 → Processing
Task 2 completes → Task 3 moves to Position 1 → Processing
```

## Database Schema

### processing_queue Table

```sql
CREATE TABLE processing_queue (
    id VARCHAR PRIMARY KEY,
    expert_id VARCHAR NOT NULL,
    agent_id VARCHAR NOT NULL,
    task_type VARCHAR(50) DEFAULT 'file_processing',
    status ENUM('queued', 'processing', 'completed', 'failed', 'cancelled'),
    priority INTEGER DEFAULT 0,
    queue_position INTEGER,
    task_data JSON,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### expert_processing_progress Updates

```sql
ALTER TABLE expert_processing_progress 
ADD COLUMN queue_position INTEGER,
ADD COLUMN task_id VARCHAR;
```

## Features

✅ **No Redis Required** - Uses PostgreSQL for queue management
✅ **Concurrent Creation** - Multiple users can create experts simultaneously
✅ **Sequential Processing** - Tasks processed one at a time to avoid resource conflicts
✅ **Priority Support** - Higher priority tasks processed first
✅ **Automatic Retries** - Failed tasks retry up to 3 times
✅ **Queue Position** - Users see their position in queue
✅ **Real-time Updates** - Progress updates every 2 seconds
✅ **Background Worker** - Runs automatically on server startup
✅ **Error Handling** - Comprehensive error tracking and reporting

## Installation

### 1. Run Migration

```bash
cd /home/kartar/CascadeProjects/dilan-ai-backend
python add_queue_table.py
```

### 2. Restart Server

```bash
python main.py
```

**Expected Output:**
```
✅ Database tables initialized successfully!
🚀 Starting background queue worker...
✅ Queue worker started!
🚀 Queue worker started - Processing tasks in background
```

## Usage

### Creating Experts (Multiple Users)

**User 1:**
```bash
POST /experts/
{
  "name": "Expert 1",
  "selected_files": ["file1.pdf"]
}
```

**Response:**
```json
{
  "success": true,
  "expert": {...},
  "file_processing": {
    "queued": true,
    "queue_position": 1,
    "task_id": "task-uuid"
  }
}
```

**User 2 (simultaneously):**
```bash
POST /experts/
{
  "name": "Expert 2",
  "selected_files": ["file2.pdf"]
}
```

**Response:**
```json
{
  "success": true,
  "expert": {...},
  "file_processing": {
    "queued": true,
    "queue_position": 2,
    "task_id": "task-uuid-2"
  }
}
```

### Checking Progress

```bash
GET /api/experts/{expert_id}/progress
```

**Response (Queued):**
```json
{
  "success": true,
  "progress": {
    "stage": "queued",
    "status": "pending",
    "queue_position": 2,
    "task_id": "task-uuid",
    "progress_percentage": 0,
    "details": {
      "message": "Waiting in queue for processing"
    }
  }
}
```

**Response (Processing):**
```json
{
  "success": true,
  "progress": {
    "stage": "embedding",
    "status": "in_progress",
    "queue_position": null,
    "progress_percentage": 45.0,
    "current_batch": 45,
    "total_batches": 100
  }
}
```

## UI Display

### Queued State
```
┌─────────────────────────────────────────┐
│  👤 Expert Name                         │
│  Description...                         │
│                                         │
│  🟡 Queued (Position 2)      Waiting... │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
│  (Pulsing animation)                    │
│                                         │
│  [Processing...] [⚙️] [🗑️]             │
└─────────────────────────────────────────┘
```

### Processing State
```
┌─────────────────────────────────────────┐
│  👤 Expert Name                         │
│  Description...                         │
│                                         │
│  🔵 Generating embeddings...      45%   │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░   │
│  File 1/1 • Batch 45/100 • Chunk 450/1000│
│                                         │
│  [Processing...] [⚙️] [🗑️]             │
└─────────────────────────────────────────┘
```

## Console Output

### Queue Worker Startup
```
🚀 Queue worker started - Processing tasks in background
```

### Task Processing
```
============================================================
📋 Processing Task: task-uuid-123
👤 Expert: expert-uuid-456
🤖 Agent: agent_xxx
📊 Task Type: file_processing
============================================================

🔄 Processing 1 files for expert expert-uuid-456
📄 Processing file file-uuid for expert expert-uuid-456
...
✅ Successfully processed document.pdf

============================================================
✅ Task Completed Successfully
📊 Files Processed: 1/1
👤 Expert: expert-uuid-456
============================================================
```

## Configuration

### Queue Worker Settings

In `services/queue_worker.py`:

```python
self.poll_interval = 2  # Check for new tasks every 2 seconds
```

### Task Retry Settings

In `models/processing_queue.py`:

```python
retry_count = Column(Integer, default=0)
max_retries = Column(Integer, default=3)
```

### Task Priority

Higher number = higher priority:

```python
queue_service.enqueue_task(
    expert_id=expert_id,
    agent_id=agent_id,
    task_data=data,
    priority=10  # High priority
)
```

## Monitoring

### Queue Status

```bash
# Get overall queue status
GET /api/queue/status
```

**Response:**
```json
{
  "queued": 3,
  "processing": 1,
  "completed": 10,
  "failed": 0,
  "total": 4
}
```

### Worker Status

```bash
# Get worker status
GET /api/queue/worker/status
```

**Response:**
```json
{
  "is_running": true,
  "current_task_id": "task-uuid-123",
  "poll_interval": 2
}
```

## Error Handling

### Task Failures

- Tasks automatically retry up to 3 times
- After 3 failures, marked as "failed"
- Error message stored in database
- User sees error on dashboard

### Worker Crashes

- Worker restarts automatically on server restart
- Queued tasks remain in database
- Processing resumes from where it left off

## Performance

### Single Worker

- Processes one task at a time
- Avoids resource conflicts
- Predictable performance

### Scalability

For high load, you can:
1. Increase worker instances (requires distributed locking)
2. Use priority queues for important tasks
3. Implement task batching

## Troubleshooting

### Queue Not Processing

**Check worker status:**
```bash
# Should see worker running
tail -f server.log | grep "Queue worker"
```

**Restart server:**
```bash
# Worker starts automatically
python main.py
```

### Tasks Stuck in Queue

**Check database:**
```sql
SELECT * FROM processing_queue WHERE status = 'queued';
```

**Manually mark as failed:**
```sql
UPDATE processing_queue 
SET status = 'failed', error_message = 'Manual intervention'
WHERE id = 'task-uuid';
```

### Progress Not Updating

**Check progress record:**
```bash
GET /api/experts/{expert_id}/progress
```

**Check task status:**
```sql
SELECT * FROM processing_queue WHERE expert_id = 'expert-uuid';
```

## Future Enhancements

- [ ] Multiple worker instances with distributed locking
- [ ] Task cancellation API
- [ ] Task pause/resume functionality
- [ ] Priority queues for VIP users
- [ ] Task scheduling (process at specific time)
- [ ] Queue analytics and statistics
- [ ] Email notifications on completion
- [ ] WebSocket for real-time updates

## Summary

The queue system provides:
- **Concurrent expert creation** without conflicts
- **Sequential processing** for reliability
- **Real-time progress** with queue position
- **Automatic retries** for failed tasks
- **No external dependencies** (no Redis required)
- **Production-ready** error handling

Users can create experts simultaneously, and the system handles everything automatically in the background! 🚀
