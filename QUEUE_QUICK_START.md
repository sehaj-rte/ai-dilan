# Queue System - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Run Migration

```bash
cd /home/kartar/CascadeProjects/dilan-ai-backend
python add_queue_table.py
```

**Expected Output:**
```
🚀 Starting migration: Add queue system tables

📊 Creating processing_queue table...
✅ Successfully created processing_queue table!

📊 Updating expert_processing_progress table...
  Adding queue_position column...
  ✅ Added queue_position column
  Adding task_id column...
  ✅ Added task_id column

✅ All tables updated successfully!
```

### Step 2: Restart Backend Server

```bash
python main.py
```

**Expected Output:**
```
✅ Database tables initialized successfully!
🚀 Starting background queue worker...
✅ Queue worker started!
🚀 Queue worker started - Processing tasks in background
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Test Concurrent Expert Creation

**Open 2 Browser Tabs:**

**Tab 1:**
1. Go to `/dashboard/create-expert`
2. Fill in expert details
3. Upload a large PDF file
4. Click "Create Expert"

**Tab 2 (Immediately after Tab 1):**
1. Go to `/dashboard/create-expert`
2. Fill in different expert details
3. Upload another file
4. Click "Create Expert"

**Both will succeed! Check dashboard:**
- Expert 1: "Queued (Position 1)" → Processing
- Expert 2: "Queued (Position 2)" → Waiting

## 📊 What You'll See

### Dashboard - Expert 1 (Processing)
```
┌─────────────────────────────────────────┐
│  👤 Expert 1                            │
│  Description...                         │
│                                         │
│  🔵 Generating embeddings...      45%   │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░   │
│  File 1/1 • Batch 45/100 • Chunk 450/1000│
│  📄 document.pdf                        │
│                                         │
│  [Processing...] [⚙️] [🗑️]             │
└─────────────────────────────────────────┘
```

### Dashboard - Expert 2 (Queued)
```
┌─────────────────────────────────────────┐
│  👤 Expert 2                            │
│  Description...                         │
│                                         │
│  🟡 Queued (Position 2)      Waiting... │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
│  (Pulsing animation)                    │
│                                         │
│  [Processing...] [⚙️] [🗑️]             │
└─────────────────────────────────────────┘
```

### Console Output
```
============================================================
📋 Processing Task: task-uuid-1
👤 Expert: expert-uuid-1
🤖 Agent: agent_xxx
📊 Task Type: file_processing
============================================================

🔄 Processing 1 files for expert expert-uuid-1
📄 Processing file file-uuid for expert expert-uuid-1
📝 Extracting text from document.pdf
✅ Extracted 50000 characters from document.pdf
🧠 Embedding Service: Processing document document.pdf
🔄 Processing batch 1/100 (chunks 1-10)
✅ Batch 1 completed: 10/10 chunks embedded
📊 Progress: 10/1000 chunks (1.0%) - Est. 130.0s remaining
...
🎉 Pinecone processing complete

============================================================
✅ Task Completed Successfully
📊 Files Processed: 1/1
👤 Expert: expert-uuid-1
============================================================

============================================================
📋 Processing Task: task-uuid-2
👤 Expert: expert-uuid-2
...
```

## ✅ Verification Checklist

- [ ] Migration ran successfully
- [ ] Server shows "Queue worker started"
- [ ] Can create multiple experts simultaneously
- [ ] First expert shows "Processing"
- [ ] Second expert shows "Queued (Position 2)"
- [ ] Progress bars update every 2 seconds
- [ ] Chat button disabled during processing
- [ ] Chat button enables when complete
- [ ] Console shows task processing logs

## 🎯 Key Features Working

✅ **Concurrent Creation** - Multiple users can create experts at the same time
✅ **Sequential Processing** - Tasks processed one at a time (no conflicts)
✅ **Queue Position** - Users see their position in queue
✅ **Real-time Updates** - Progress updates every 2 seconds
✅ **Pulsing Animation** - Queued tasks show pulsing progress bar
✅ **Automatic Processing** - Background worker handles everything
✅ **Chat Disabled** - Can't chat until processing complete
✅ **Error Handling** - Failed tasks retry automatically

## 🔍 Monitoring

### Check Queue Status

```bash
# In Python console or script
from config.database import SessionLocal
from services.queue_service import QueueService

db = SessionLocal()
queue_service = QueueService(db)
status = queue_service.get_queue_status()
print(status)
# Output: {'queued': 2, 'processing': 1, 'completed': 5, 'failed': 0, 'total': 3}
```

### Check Progress

```bash
curl http://localhost:8000/api/experts/{expert_id}/progress
```

### View All Queued Tasks

```sql
SELECT id, expert_id, status, queue_position, created_at 
FROM processing_queue 
WHERE status = 'queued' 
ORDER BY queue_position;
```

## 🐛 Troubleshooting

### Worker Not Starting

**Check logs:**
```bash
# Should see "Queue worker started"
python main.py
```

**If not starting:**
```python
# Check for errors in startup_event
# Look for import errors or database connection issues
```

### Tasks Not Processing

**Check worker is running:**
```bash
# Look for "Processing Task" logs
tail -f server.log
```

**Manually trigger (if needed):**
```python
from services.queue_worker import get_worker
import asyncio

worker = get_worker()
asyncio.run(worker.start())
```

### Progress Not Showing

**Check progress record exists:**
```bash
curl http://localhost:8000/api/experts/{expert_id}/progress
```

**Check task in queue:**
```sql
SELECT * FROM processing_queue WHERE expert_id = '{expert_id}';
```

## 📚 Documentation

- **Full Guide**: `QUEUE_SYSTEM.md`
- **Progress Tracking**: `PROGRESS_TRACKING.md`
- **API Reference**: http://localhost:8000/docs

## 🎉 Success!

Your queue system is now fully operational! Multiple users can create experts simultaneously, and the system will:

1. ✅ Queue all tasks automatically
2. ✅ Process them sequentially
3. ✅ Show queue position to users
4. ✅ Update progress in real-time
5. ✅ Handle errors with retries
6. ✅ Enable chat when complete

**Enjoy your production-ready queue system! 🚀**
