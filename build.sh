#!/bin/bash
# Build script for Render deployment

echo "=== Starting build process ==="

# Install requirements
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p static templates sessions logs

# Set proper permissions
echo "Setting permissions..."
chmod -R 755 .
chmod +x server.py
chmod +x environment_check.py

# Ensure all Python files are executable
find . -name "*.py" -exec chmod +x {} \;

# Create log files with proper permissions
touch fb_auth.log
touch environment_check.log
chmod 644 *.log

# Run environment check to get diagnostic info
echo "Running environment check..."
python environment_check.py

# Set environment variables if not already set
if [ -z "$PORT" ]; then
    export PORT=10000
fi

if [ -z "$DEBUG" ]; then
    export DEBUG=false
fi

echo "=== Build completed successfully! ==="
echo "Configuration:"
echo "PORT=$PORT"
echo "DEBUG=$DEBUG"