# Database Migrations

## Running the Folder Migration

To add the folder field to your existing database, run:

```bash
# Using psql
psql -h your-host -U your-user -d your-database -f migrations/add_folder_column.sql

# Or using the connection string from your .env
psql $DATABASE_URL -f migrations/add_folder_column.sql
```

## What This Migration Does

1. Adds a `folder` column to the `files` table
2. Sets default value to "Uncategorized" for all existing files
3. Creates an index on the folder column for better performance

## Verification

After running the migration, you should see output showing files grouped by folder.

All existing files will be in the "Uncategorized" folder by default.
