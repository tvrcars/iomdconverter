#!/bin/bash
set -e  # Exit on error

# Set up logging to a file
LOGFILE="/home/LogFiles/startup.log"
exec 1> >(tee -a "$LOGFILE") 2>&1

echo "Starting startup script at $(date)"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"

# Try to get root permissions and install dependencies
if [ "$EUID" -ne 0 ]; then 
    echo "Attempting to run with sudo..."
    sudo apt-get update -y || echo "Failed to run apt-get update with sudo"
    sudo apt-get install -y wget libgl1-mesa-glx pandoc || echo "Failed to install dependencies with sudo"
else
    echo "Running as root..."
    apt-get update -y || echo "Failed to run apt-get update"
    apt-get install -y wget libgl1-mesa-glx pandoc || echo "Failed to install dependencies"
fi

# Manual pandoc installation
echo "Checking pandoc installation..."
if ! command -v pandoc &> /dev/null; then
    echo "Pandoc not found in PATH, attempting manual installation..."
    cd /tmp
    wget https://github.com/jgm/pandoc/releases/download/3.1.2/pandoc-3.1.2-linux-amd64.tar.gz
    tar xvzf pandoc-3.1.2-linux-amd64.tar.gz
    sudo mv pandoc-3.1.2/bin/pandoc /usr/local/bin/
    rm -rf pandoc-3.1.2*
    cd -
fi

# Environment information
echo "PATH environment: $PATH"
echo "Current directory contents:"
ls -la
echo "Pandoc location:"
which pandoc || echo "Pandoc not found in PATH"
echo "Pandoc version:"
pandoc --version || echo "Failed to get pandoc version"

echo "Startup script completed at $(date)"

# Start gunicorn
gunicorn --bind=0.0.0.0:8000 app:app