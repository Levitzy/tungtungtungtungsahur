#!/bin/bash
# Simplified build script for Render

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setting up environment..."
mkdir -p sessions logs

echo "Setting permissions..."
chmod +x server.py

echo "Build complete!"