#!/bin/bash
set -e  # Exit on error

# Add error logging
exec 1> >(logger -s -t $(basename $0)) 2>&1

echo "Starting startup script..."

# Try to get root permissions
if [ "$EUID" -ne 0 ]; then 
    echo "Attempting to run with sudo..."
    sudo apt-get update || echo "Failed to run apt-get update with sudo"
    sudo apt-get install -y libgl1-mesa-glx pandoc || echo "Failed to install dependencies with sudo"
else
    echo "Running as root..."
    apt-get update || echo "Failed to run apt-get update"
    apt-get install -y libgl1-mesa-glx pandoc || echo "Failed to install dependencies"
fi

echo "Checking pandoc installation..."
which pandoc || echo "Pandoc not found in PATH"
pandoc --version || echo "Failed to get pandoc version"

echo "Startup script completed"

# Start gunicorn
gunicorn --bind=0.0.0.0:8000 app:app