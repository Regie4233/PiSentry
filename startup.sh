#!/bin/bash

# Configuration
# Get the directory where the script is located
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="$APP_DIR/startup.log"

# Function to log messages with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Ensure log file exists
touch "$LOG_FILE"

log_message "Starting PiSentry application..."

# Navigate to application directory
cd "$APP_DIR" || {
    log_message "Error: Could not change directory to $APP_DIR"
    exit 1
}

# Force Hotspot Mode using wifi_switch.sh
if [ -f "./wifi_switch.sh" ]; then
    log_message "Configuring network..."
    chmod +x ./wifi_switch.sh
    ./wifi_switch.sh force >> "$LOG_FILE" 2>&1
else
    log_message "Warning: wifi_switch.sh not found."
fi

# Activate Virtual Environment
if [ -d ".venv" ]; then
    log_message "Activating virtual environment..."
    source .venv/bin/activate
else
    log_message "Error: Virtual environment (.venv) not found."
    exit 1
fi

# Start the Python Application
log_message "Launching main.py..."
python main.py >> "$LOG_FILE" 2>&1 &

APP_PID=$!
log_message "Application started with PID $APP_PID"

# Wait for the process
wait $APP_PID
