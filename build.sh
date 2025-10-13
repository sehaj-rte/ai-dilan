#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
python init_db.py
python add_progress_table.py
python add_queue_table.py
python migrate_files_table.py
