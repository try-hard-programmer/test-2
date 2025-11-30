#!/bin/bash

# Telegram Dashboard Startup Script

echo "Starting Telegram Dashboard..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed!"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Run the application
echo "Starting server on http://127.0.0.1:8000"
uv run python main.py
