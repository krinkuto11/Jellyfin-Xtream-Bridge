#!/bin/bash

# Quick start script for Jellyfin-Xtream Server

echo "=================================="
echo "Jellyfin-Xtream Server Startup"
echo "=================================="

# Check if config.json exists
if [ ! -f "config/config.json" ]; then
    echo "Error: config/config.json not found!"
    echo "Please copy config.json.example to config.json and configure it:"
    echo "  cp config/config.json.example config/config.json"
    echo "  nano config/config.json"
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python3 -c "import requests, flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo "Starting Jellyfin-Xtream Server..."
python3 src/xtream_server.py
