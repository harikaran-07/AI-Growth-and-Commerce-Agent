#!/bin/bash
# Unified build script for MerchantFlow AI
# Builds the Next.js frontend and installs Python backend dependencies

set -e

echo "=== Building MerchantFlow AI ==="

# Install Python dependencies
echo "Installing Python dependencies..."
cd backend
pip install -r requirements.txt

# Build Next.js frontend
echo "Building Next.js frontend..."
cd ../frontend
npm install
npm run build

# Verify the static export was created
if [ -d "out/_next" ]; then
    echo "Frontend build successful - static export created in frontend/out/"
else
    echo "ERROR: Frontend build failed - out/_next not found"
    exit 1
fi

cd ..
echo "=== Build complete ==="
