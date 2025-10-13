# Quick Start: Progress Tracking System

## 🚀 Get Started in 3 Steps

### Step 1: Run Database Migration

```bash
cd /home/kartar/CascadeProjects/dilan-ai-backend
python add_progress_table.py
```

**Expected Output:**
```
🚀 Starting migration: Add expert_processing_progress table

📊 Creating expert_processing_progress table...
✅ Successfully created expert_processing_progress table!

Table structure:
  - id (UUID, primary key)
  - expert_id (String, indexed)
  - agent_id (String)
  - stage (String)
  - status (String)
  ...

✅ Migration completed successfully!
```

### Step 2: Restart Backend Server

```bash
# Stop the current server (Ctrl+C if running)
python main.py
```

**Expected Output:**
```
✅ Database tables initialized successfully!
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Test the System

1. **Open Dashboard**: Navigate to `http://localhost:3000/dashboard`

2. **Create Expert with Files**:
   - Click "Create Expert" button
   - Fill in expert details
   - Upload one or more files (PDF, DOCX, etc.)
   - Click "Create Expert"

3. **Watch Progress**:
   - You'll be redirected to dashboard
   - Find your new expert card
   - See the progress bar appear automatically
   - Watch it update every 2 seconds

4. **Progress Stages**:
   - 🔄 **Processing files...** (0-10%)
   - 📝 **Extracting text...** (10-20%)
   - 🧠 **Generating embeddings...** (20-90%) ← Most time here
   - 💾 **Storing in database...** (90-100%)
   - ✅ **Complete!** (100%)

5. **Chat When Ready**:
   - Chat button is disabled during processing
   - Once complete (100%), chat button enables
   - Click "Chat" to start conversation

## 📊 What You'll See

### Dashboard During Processing

```
┌─────────────────────────────────────────┐
│  👤 Expert Name                         │
│  Description text here...               │
│                                         │
│  🟢 Active    Created: Jan 10, 2025    │
│  Agent ID: agent_4701k772vmds...       │
│                                         │
│  🧠 Generating embeddings...      45%   │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░   │
│  File 1/1 • Batch 45/100 • Chunk 450/1000│
│  📄 document.pdf                        │
│                                         │
│  [Processing...] [⚙️] [🗑️]             │
└─────────────────────────────────────────┘
```

### Dashboard After Completion

```
┌─────────────────────────────────────────┐
│  👤 Expert Name                         │
│  Description text here...               │
│                                         │
│  🟢 Active    Created: Jan 10, 2025    │
│  Agent ID: agent_4701k772vmds...       │
│                                         │
│  [Chat] [⚙️] [🗑️]                      │
└─────────────────────────────────────────┘
```

## 🔍 Verify Installation

### Check Database Table

```bash
# Connect to PostgreSQL
psql -U your_user -d dilan_ai

# Check if table exists
\dt expert_processing_progress

# View table structure
\d expert_processing_progress

# Exit
\q
```

### Test API Endpoints

```bash
# Get progress for an expert (replace with actual expert_id)
curl http://localhost:8000/api/experts/YOUR_EXPERT_ID/progress

# Get all active progress records
curl http://localhost:8000/api/experts/progress/active
```

### Check Backend Logs

Look for these log messages during expert creation:

```
🚀 Starting Pinecone processing for expert xxx with 1 files
📄 Processing file yyy for expert xxx
📝 Extracting text from document.pdf
✅ Extracted 50000 characters from document.pdf
🧠 Embedding Service: Processing document document.pdf
🔄 Processing batch 1/100 (chunks 1-10)
✅ Batch 1 completed: 10/10 chunks embedded
📊 Progress: 10/1000 chunks (1.0%) - Est. 130.0s remaining
...
🎉 Pinecone processing complete for expert xxx
```

## ⚠️ Troubleshooting

### Progress Not Showing?

**Check 1: Table exists?**
```bash
python add_progress_table.py
```

**Check 2: Backend running?**
```bash
# Should see server running on port 8000
curl http://localhost:8000/health
```

**Check 3: Frontend polling?**
```
Open browser console (F12)
Look for API calls to /api/experts/.../progress
```

### Progress Stuck?

**Check backend logs:**
```bash
# Look for errors in terminal where backend is running
# Common issues:
# - OpenAI API key invalid
# - Pinecone connection failed
# - File content not accessible
```

**Check progress record:**
```bash
curl http://localhost:8000/api/experts/YOUR_EXPERT_ID/progress
# Look at "error_message" field
```

### Chat Button Still Disabled?

**Check progress status:**
```bash
curl http://localhost:8000/api/experts/YOUR_EXPERT_ID/progress
# Status should be "completed"
# Stage should be "complete"
# Progress_percentage should be 100.0
```

**Force refresh:**
```
Press Ctrl+Shift+R in browser to hard refresh
```

## 📚 More Information

- **Full Documentation**: See `PROGRESS_TRACKING.md`
- **Implementation Details**: See `PROGRESS_IMPLEMENTATION_SUMMARY.md`
- **API Reference**: Check FastAPI docs at `http://localhost:8000/docs`

## 🎯 Expected Processing Times

File processing time depends on file size and content:

- **Small file (1-10 pages)**: 10-30 seconds
- **Medium file (10-50 pages)**: 30-120 seconds  
- **Large file (50-200 pages)**: 2-10 minutes
- **Very large file (200+ pages)**: 10+ minutes

Most time is spent in the **embedding generation** stage (20-90% progress).

## ✅ Success Checklist

- [ ] Migration script ran successfully
- [ ] Backend server restarted
- [ ] Can create expert with files
- [ ] Progress bar appears on dashboard
- [ ] Progress updates every 2 seconds
- [ ] See detailed stage information
- [ ] Chat button disabled during processing
- [ ] Chat button enables when complete
- [ ] Can chat with expert after completion

## 🎉 You're Done!

Your progress tracking system is now fully operational. Users will see beautiful real-time progress bars whenever they create experts with files.

**Enjoy the enhanced user experience! 🚀**
