# Database Migration Guide

## Overview
This guide explains how to run database migrations for the Dilan AI Backend.

## Current Issue
The production database is missing several columns in the `files` table that were added to the model but not migrated to the database.

### Missing Columns:
- `content` - For storing file content as fallback when S3 is unavailable
- `description` - User-provided description
- `tags` - JSON array of tags for categorization
- `document_type` - Auto-detected file type (pdf, docx, image, etc.)
- `language` - Detected language
- `word_count` - Extracted word count
- `page_count` - Number of pages (for PDFs)
- `processing_status` - Processing status (pending, processing, completed, failed)
- `processing_error` - Error message if processing failed
- `extracted_text` - Full extracted text content
- `extracted_text_preview` - First 500 chars for preview
- `has_images` - Boolean flag for images
- `has_tables` - Boolean flag for tables

## How to Run Migration

### Option 1: Run Locally (Recommended for Testing)

1. **Ensure you have the correct DATABASE_URL in your `.env` file**
   ```bash
   # For local PostgreSQL
   DATABASE_URL=postgresql://username:password@localhost:5432/dilan_ai
   
   # For production (Render)
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   ```

2. **Run the migration script**
   ```bash
   python migrate_files_table.py
   ```

3. **Expected Output**
   ```
   🔗 Connecting to database...
   ✅ Found 'files' table
   
   📋 Checking for missing columns...
   
   ✅ Added column 'content' (BYTEA)
   ✅ Added column 'description' (TEXT)
   ✅ Added column 'tags' (JSON)
   ...
   
   ============================================================
   📊 Migration Summary:
      ✅ Columns added: 13
      ⏭️  Columns skipped (already exist): 0
   ============================================================
   
   🎉 Migration completed successfully!
   ```

### Option 2: Run on Render (Production)

#### Method A: Using Render Shell
1. Go to your Render dashboard
2. Select your backend service
3. Click "Shell" tab
4. Run:
   ```bash
   python migrate_files_table.py
   ```

#### Method B: SSH into Render
1. Install Render CLI if not already installed
2. SSH into your service:
   ```bash
   render ssh <your-service-name>
   ```
3. Run the migration:
   ```bash
   python migrate_files_table.py
   ```

#### Method C: Add to Build Script (One-time)
1. Edit `build.sh` to include migration:
   ```bash
   #!/usr/bin/env bash
   set -o errexit
   
   pip install -r requirements.txt
   
   # Run migration
   python migrate_files_table.py
   ```
2. Commit and push - Render will run it on next deploy
3. **Important:** Remove the migration line after first successful deploy to avoid running it repeatedly

### Option 3: Manual SQL (Advanced)

If you prefer to run SQL directly:

```sql
-- Connect to your database and run:

ALTER TABLE files ADD COLUMN content BYTEA;
ALTER TABLE files ADD COLUMN description TEXT;
ALTER TABLE files ADD COLUMN tags JSON;
ALTER TABLE files ADD COLUMN document_type VARCHAR(50);
ALTER TABLE files ADD COLUMN language VARCHAR(10);
ALTER TABLE files ADD COLUMN word_count INTEGER;
ALTER TABLE files ADD COLUMN page_count INTEGER;
ALTER TABLE files ADD COLUMN processing_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE files ADD COLUMN processing_error TEXT;
ALTER TABLE files ADD COLUMN extracted_text TEXT;
ALTER TABLE files ADD COLUMN extracted_text_preview TEXT;
ALTER TABLE files ADD COLUMN has_images BOOLEAN DEFAULT FALSE;
ALTER TABLE files ADD COLUMN has_tables BOOLEAN DEFAULT FALSE;
```

## Verification

After running the migration, verify it worked:

```bash
# Test the API endpoint
curl https://your-backend-url.onrender.com/knowledge-base/files

# Should return files without database errors
```

## Troubleshooting

### Error: "column already exists"
This is safe to ignore - it means the column was already added in a previous migration.

### Error: "relation 'files' does not exist"
The files table hasn't been created yet. Run:
```bash
python init_db.py
```

### Error: "DATABASE_URL not found"
Make sure your `.env` file has the DATABASE_URL variable set, or set it in your environment:
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

## Future Migrations

For future schema changes:
1. Update the model in `models/file_db.py` (or other model files)
2. Create a new migration script (e.g., `migrate_add_xyz_column.py`)
3. Run the migration on production
4. Document it in this guide

## Notes

- The migration script is **idempotent** - it's safe to run multiple times
- It will skip columns that already exist
- Always test on a local/staging database first
- Consider using Alembic for more complex migrations in the future
