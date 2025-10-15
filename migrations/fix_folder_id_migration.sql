-- Migration: Fix folder_id relationships and migrate existing data
-- This migration handles the case where folder_id column already exists

-- Step 1: Create an "Uncategorized" folder if it doesn't exist
INSERT INTO folders (id, name, user_id, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    'Uncategorized',
    NULL::uuid,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM folders WHERE name = 'Uncategorized'
);

-- Step 2: Create folders for all existing folder names in files table
INSERT INTO folders (id, name, user_id, created_at, updated_at)
SELECT DISTINCT
    gen_random_uuid(),
    folder,
    NULL::uuid,
    NOW(),
    NOW()
FROM files 
WHERE folder IS NOT NULL 
AND folder != 'Uncategorized'
AND NOT EXISTS (
    SELECT 1 FROM folders WHERE name = files.folder
);

-- Step 3: Update files table to set folder_id based on folder name
UPDATE files 
SET folder_id = folders.id 
FROM folders 
WHERE files.folder = folders.name
AND files.folder_id IS NULL;

-- Step 4: Set folder_id to Uncategorized for any files without a folder_id
UPDATE files 
SET folder_id = (
    SELECT id FROM folders WHERE name = 'Uncategorized' LIMIT 1
)
WHERE folder_id IS NULL;

-- Step 5: Add NOT NULL constraint to folder_id (after all data is migrated)
ALTER TABLE files ALTER COLUMN folder_id SET NOT NULL;
