#!/bin/bash

# Determine which service to start based on environment variable
if [ "$SERVICE" = "frontend" ]; then
    echo "Starting frontend service..."
    cd front_end
    npm install
    npm run build
    npx vite preview --host 0.0.0.0 --port ${PORT:-3000}
else
    echo "Starting backend service..."
    cd back_end
    python3 -m pip install --no-cache-dir -r requirements.txt
    python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
fi
