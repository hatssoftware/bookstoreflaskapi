#!/bin/bash

# Cron job script to modify books every 12 hours
# Add to crontab with: 0 */12 * * * /path/to/your/project/cron_job.sh

# Change to the project directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Log timestamp
echo "[$(date)] Starting book modification cron job"

# Modify 10-150 random books (random count for more realistic simulation)
count=$((RANDOM % 141 + 10))  # Random number between 10-150

# Run the modification script quietly
python3 modify_books.py --count $count --quiet

# Log completion
echo "[$(date)] Completed book modification cron job" 