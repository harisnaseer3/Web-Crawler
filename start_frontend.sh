#!/bin/bash

echo "Web Crawler Search Engine - Frontend Startup"
echo "================================================"

cd frontend

echo "Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "Failed to install dependencies. Please check Node.js installation."
    exit 1
fi

echo ""
echo "Starting React development server..."
echo "Frontend will be available at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================================"

npm start
