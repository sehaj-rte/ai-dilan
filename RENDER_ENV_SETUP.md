# Render Environment Variables Setup

## Database Configuration for Neon

Your Neon database connection has `channel_binding=require` which can cause issues with SQLAlchemy.

### Option 1: Update DATABASE_URL (Recommended)

Remove the `channel_binding=require` parameter from your DATABASE_URL:

```
DATABASE_URL=postgresql://neondb_owner:npg_GCO60HULTPmx@ep-weathered-shape-adu1rbm6-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require
```

### Option 2: Use Individual Database Variables

Instead of using DATABASE_URL, set these individual variables:

```
DB_HOST=ep-weathered-shape-adu1rbm6-pooler.c-2.us-east-1.aws.neon.tech
DB_PORT=5432
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=npg_GCO60HULTPmx
```

Then update `config/database.py` to build the URL from these variables.

### Steps to Update on Render:

1. Go to your Render Dashboard
2. Click on your backend service
3. Go to "Environment" tab
4. Find `DATABASE_URL` variable
5. Update it to remove `&channel_binding=require`
6. Save changes
7. Render will automatically redeploy

## Current Fix

The code now automatically removes `channel_binding=require` from the DATABASE_URL if present, so you can keep your current configuration and just redeploy.
