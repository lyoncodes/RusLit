#!/bin/bash

# Absolute path to your virtualenv
VENV_PATH="/app/venv"
PROJECT_PATH="/app"
LOG_FILE="$PROJECT_PATH/gutenberg_cron.log"

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Run the script with Flask app context
python "$PROJECT_PATH/run_gutenberg_cron.py" >> "$LOG_FILE" 2>&1
