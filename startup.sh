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
if ! command -v pandoc &> /dev/null; then
    echo "Pandoc could not be found, attempting manual installation..."
    wget https://github.com/jgm/pandoc/releases/download/3.1.2/pandoc-3.1.2-linux-amd64.tar.gz
    tar -xvzf pandoc-3.1.2-linux-amd64.tar.gz --strip-components 1 -C /usr/local
    rm pandoc-3.1.2-linux-amd64.tar.gz
fi

which pandoc || echo "Pandoc not found in PATH"
pandoc --version || echo "Failed to get pandoc version"

echo "Startup script completed"

# Start gunicorn
gunicorn --bind=0.0.0.0:8000 app:app