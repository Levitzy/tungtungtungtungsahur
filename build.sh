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

# Ensure all Python files are executable
find . -name "*.py" -exec chmod +x {} \;

# Create log files with proper permissions
touch fb_auth.log
chmod 644 *.log

# Set environment variables if not already set
if [ -z "$PORT" ]; then
    export PORT=10000
fi

if [ -z "$DEBUG" ]; then
    export DEBUG=true
fi

echo "=== Build completed successfully! ==="
echo "Configuration:"
echo "PORT=$PORT"
echo "DEBUG=$DEBUG"