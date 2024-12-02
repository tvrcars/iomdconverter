#!/bin/bash
set -e  # Exit on error

# Add error logging
exec 1> >(logger -s -t $(basename $0)) 2>&1

echo "Starting startup script..."
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"

# Try to get root permissions
if [ "$EUID" -ne 0 ]; then 
    echo "Attempting to run with sudo..."
    sudo apt-get update || echo "Failed to run apt-get update with sudo"
    sudo apt-get install -y libgl1-mesa-glx || echo "Failed to install libgl1-mesa-glx with sudo"
    
    # Force pypandoc to download pandoc
    echo "Forcing pypandoc to download pandoc..."
    python -c "import pypandoc; pypandoc.download_pandoc()" || echo "Failed to download pandoc through pypandoc"
else
    echo "Running as root..."
    apt-get update || echo "Failed to run apt-get update"
    apt-get install -y libgl1-mesa-glx || echo "Failed to install libgl1-mesa-glx"
    
    # Force pypandoc to download pandoc
    echo "Forcing pypandoc to download pandoc..."
    python -c "import pypandoc; pypandoc.download_pandoc()" || echo "Failed to download pandoc through pypandoc"
fi

# Print environment information for debugging
echo "PATH environment: $PATH"
echo "Python version:"
python --version
echo "Pip version:"
pip --version
echo "Installed Python packages:"
pip list

echo "Checking pandoc installation..."
which pandoc || echo "Pandoc not found in PATH"
pandoc --version || echo "Failed to get pandoc version"

echo "Startup script completed"

# Start gunicorn
gunicorn --bind=0.0.0.0:8000 app:app