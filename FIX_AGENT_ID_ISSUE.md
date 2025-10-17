# Fix for agent_id and project_id Being NULL in Database

## Problem Summary

When adding content via voice notes, YouTube transcriptions, or website scraping, the `agent_id` and `project_id` columns in the `files` table were being stored as `NULL` instead of the actual agent ID values.

## Root Cause

The issue was caused by **foreign key constraints** on the `agent_id` column in both the `files` and `folders` tables:

```sql
-- Old schema (PROBLEMATIC)
ALTER TABLE files ADD COLUMN agent_id VARCHAR REFERENCES experts(id)
ALTER TABLE folders ADD COLUMN agent_id VARCHAR REFERENCES experts(id)
```

The foreign key constraint expected the `agent_id` to reference `experts.id` (which is a UUID string like `"73128da3-a5c4-4cd1-b86d-bd64c00680da"`), but the application code was trying to store the **expert's database ID** (also a UUID), not the ElevenLabs agent ID.

However, there was confusion in the codebase about what should be stored:
- Some parts of the code tried to store ElevenLabs agent IDs (like `"agent_bdrk_..."`)
- Other parts correctly stored the expert's database ID

When the foreign key constraint validation failed (because the value didn't exist in the `experts.id` column), the database rejected the value and stored `NULL` instead.

## Solution

### 1. Remove Foreign Key Constraints from Models

**Updated `models/file_db.py`:**
```python
# Before:
agent_id = Column(String, ForeignKey('experts.id'), nullable=True)
project_id = Column(String, ForeignKey('experts.id'), nullable=True)

# After:
agent_id = Column(String, nullable=True)  # Agent isolation (stores expert database ID)
project_id = Column(String, nullable=True)  # Deprecated: use agent_id instead
```

**Updated `models/folder_db.py`:**
```python
# Before:
agent_id = Column(String, ForeignKey('experts.id'), nullable=True)

# After:
agent_id = Column(String, nullable=True)  # Agent isolation (stores expert database ID)
```

### 2. Add Missing agent_id Parameters

**Updated Controller Functions:**
- `transcribe_and_save_audio()` - Added `agent_id` parameter
- `transcribe_youtube_video()` - Added `agent_id` parameter
- `scrape_and_save_website()` - Added `agent_id` parameter

**Updated API Routes:**
- `/transcribe-audio` - Added `agent_id` form parameter
- `/transcribe-youtube` - Added `agent_id` to request model
- `/scrape-website` - Added `agent_id` to request model

### 3. Run Database Migration

A migration script has been created to remove the foreign key constraints from the existing database:

```bash
python migrations/fix_agent_id_constraint.py
```

This script will:
1. Find and remove all foreign key constraints on `files.agent_id`
2. Find and remove all foreign key constraints on `folders.agent_id`
3. Allow the application to store expert database IDs without constraint validation

## What to Store in agent_id

**IMPORTANT:** The `agent_id` column should store the **expert's database ID** (UUID from `experts.id`), NOT the ElevenLabs agent ID.

Example:
- ✅ Correct: `"73128da3-a5c4-4cd1-b86d-bd64c00680da"` (expert database ID)
- ❌ Wrong: `"agent_bdrk_abc123..."` (ElevenLabs agent ID)

The ElevenLabs agent ID is stored separately in the `experts.elevenlabs_agent_id` column.

## Testing the Fix

After applying these changes:

1. **Run the migration:**
   ```bash
   cd ai-dilan
   python migrations/fix_agent_id_constraint.py
   ```

2. **Restart your backend server**

3. **Test voice note transcription:**
   - Upload a voice note
   - Check the database to verify `agent_id` and `project_id` are populated

4. **Test YouTube transcription:**
   - Transcribe a YouTube video
   - Check the database to verify `agent_id` and `project_id` are populated

5. **Test website scraping:**
   - Scrape a website
   - Check the database to verify `agent_id` and `project_id` are populated

## Files Modified

1. `models/file_db.py` - Removed foreign key constraints
2. `models/folder_db.py` - Removed foreign key constraints
3. `controllers/knowledge_base_controller.py` - Added agent_id parameters to functions
4. `routes/knowledge_base.py` - Added agent_id to API routes and request models
5. `migrations/fix_agent_id_constraint.py` - New migration script

## Additional Notes

- The `project_id` column is deprecated and should use `agent_id` instead
- Both columns are set to the same value (expert database ID) for backward compatibility
- The frontend needs to pass the expert's database ID (not ElevenLabs agent ID) when calling these endpoints
