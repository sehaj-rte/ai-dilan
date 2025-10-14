-- Drop table if exists (for clean migration)
DROP TABLE IF EXISTS folders CASCADE;

-- Create folders table
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT unique_folder_per_user UNIQUE(name, user_id)
);

-- Create index for faster lookups
CREATE INDEX idx_folders_user_id ON folders(user_id);
CREATE INDEX idx_folders_name ON folders(name);

-- Insert default "Uncategorized" folder
INSERT INTO folders (name, user_id) 
VALUES ('Uncategorized', NULL)
ON CONFLICT (name, user_id) DO NOTHING;

-- Migrate existing folders from files table
INSERT INTO folders (name, user_id)
SELECT DISTINCT folder, user_id
FROM files
WHERE folder IS NOT NULL 
  AND folder != 'Uncategorized'
ON CONFLICT (name, user_id) DO NOTHING;
