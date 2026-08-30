#!/bin/bash
# Unified build script for MerchantFlow AI
# Installs Python backend dependencies
# Frontend is pre-built in frontend/out/ (committed to repo)

set -e

echo "=== Building MerchantFlow AI ==="

# Install Python dependencies
echo "Installing Python dependencies..."
cd backend
pip install -r requirements.txt

cd ..
echo "=== Build complete ==="
echo "Frontend static files are in frontend/out/ (pre-built)"
