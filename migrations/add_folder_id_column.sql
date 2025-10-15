-- Migration: Add folder_id column to files table and migrate existing data
-- This migration adds proper folder relationships using UUIDs instead of folder names

-- Step 1: Add folder_id column to files table
ALTER TABLE files ADD COLUMN folder_id UUID REFERENCES folders(id);

-- Step 2: Create an "Uncategorized" folder if it doesn't exist
INSERT INTO folders (id, name, user_id, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    'Uncategorized',
    NULL,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM folders WHERE name = 'Uncategorized'
);

-- Step 3: Create folders for all existing folder names in files table
INSERT INTO folders (id, name, user_id, created_at, updated_at)
SELECT DISTINCT
    gen_random_uuid(),
    folder,
    NULL,
    NOW(),
    NOW()
FROM files 
WHERE folder IS NOT NULL 
AND folder != 'Uncategorized'
AND NOT EXISTS (
    SELECT 1 FROM folders WHERE name = files.folder
);

-- Step 4: Update files table to set folder_id based on folder name
UPDATE files 
SET folder_id = folders.id 
FROM folders 
WHERE files.folder = folders.name;

-- Step 5: Set folder_id to Uncategorized for any files without a folder_id
UPDATE files 
SET folder_id = (
    SELECT id FROM folders WHERE name = 'Uncategorized' LIMIT 1
)
WHERE folder_id IS NULL;

-- Step 6: Add NOT NULL constraint to folder_id (after all data is migrated)
ALTER TABLE files ALTER COLUMN folder_id SET NOT NULL;

-- Note: We keep the 'folder' column for now to maintain backward compatibility
-- It can be removed in a future migration once all code is updated
