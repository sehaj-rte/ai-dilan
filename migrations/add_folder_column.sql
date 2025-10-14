-- Migration: Add folder column to files table
-- Date: 2025-10-14
-- Description: Adds folder field for organizing files into categories

-- Add folder column with default value
ALTER TABLE files 
ADD COLUMN IF NOT EXISTS folder VARCHAR(255) DEFAULT 'Uncategorized' NOT NULL;

-- Update existing NULL values to 'Uncategorized' (if any)
UPDATE files 
SET folder = 'Uncategorized' 
WHERE folder IS NULL;

-- Create index on folder for better query performance
CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder);

-- Verify the migration
SELECT COUNT(*) as total_files, folder 
FROM files 
GROUP BY folder 
ORDER BY folder;
