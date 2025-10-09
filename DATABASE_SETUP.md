# Database Setup Guide

This guide will help you set up PostgreSQL for the Dilan AI Backend.

## Prerequisites

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # macOS (using Homebrew)
   brew install postgresql
   
   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Start PostgreSQL Service**
   ```bash
   # Ubuntu/Debian
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   
   # macOS
   brew services start postgresql
   ```

## Database Setup

1. **Create Database and User**
   ```bash
   # Switch to postgres user
   sudo -u postgres psql
   
   # In PostgreSQL shell:
   CREATE DATABASE dilan_ai_db;
   CREATE USER dilan_user WITH ENCRYPTED PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE dilan_ai_db TO dilan_user;
   \q
   ```

2. **Update Environment Variables**
   
   Copy `.env.example` to `.env` and update the database configuration:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file:
   ```env
   # Database Configuration
   DATABASE_URL=postgresql://dilan_user:your_secure_password@localhost:5432/dilan_ai_db
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=dilan_ai_db
   DB_USER=dilan_user
   DB_PASSWORD=your_secure_password
   ```

3. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database Tables**
   
   Option A - Automatic (recommended):
   ```bash
   python start.py
   ```
   Tables will be created automatically on startup.
   
   Option B - Manual:
   ```bash
   python init_db.py
   ```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

## Verification

1. **Check Database Connection**
   ```bash
   psql -h localhost -U dilan_user -d dilan_ai_db
   ```

2. **Verify Tables**
   ```sql
   \dt
   SELECT * FROM users;
   ```

3. **Test API Endpoints**
   ```bash
   # Start the server
   python start.py
   
   # Test registration
   curl -X POST "http://localhost:8000/auth/register" \
        -H "Content-Type: application/json" \
        -d '{
          "email": "test@example.com",
          "username": "testuser",
          "password": "testpass123",
          "full_name": "Test User"
        }'
   ```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure PostgreSQL is running
   - Check if the port 5432 is available
   - Verify database credentials

2. **Permission Denied**
   - Check user permissions on the database
   - Ensure the user has CREATE privileges

3. **Table Already Exists**
   - This is normal if you restart the server
   - Tables are created only if they don't exist

### Reset Database
```bash
# Drop and recreate database
sudo -u postgres psql
DROP DATABASE dilan_ai_db;
CREATE DATABASE dilan_ai_db;
GRANT ALL PRIVILEGES ON DATABASE dilan_ai_db TO dilan_user;
\q

# Restart the server to recreate tables
python start.py
```

## Migration (Future)

For production deployments, consider using Alembic for database migrations:
```bash
# Initialize Alembic (when needed)
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```
