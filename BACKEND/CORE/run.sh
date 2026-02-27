#!/bin/bash

# Jiomart Automation Starter for Linux
echo "🚀 JioMart Automation Starter (Linux)"

# Go to script directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "env" ]; then
    source env/bin/activate
fi

# Start FastAPI in background
echo "[1/2] ⚙️ Starting FastAPI Backend..."
python3 main_async.py &
BACKEND_PID=$!

sleep 3

# Start Telegram Bot
echo "[2/2] 🤖 Starting Telegram Bot..."
python3 interactive_bot_playwright.py

# When bot stops, kill backend too
kill $BACKEND_PID
