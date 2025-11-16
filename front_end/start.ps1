# Movie Recommender Frontend Start Script
# This script installs dependencies if needed and starts the Vite dev server

Write-Host "Starting Movie Recommender Frontend..." -ForegroundColor Cyan

# Check if node_modules exists
if (-not (Test-Path ".\node_modules")) {
    Write-Host "node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Check if .env file exists
if (-not (Test-Path ".\.env")) {
    Write-Host "Warning: .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".\.env.example") {
        Copy-Item .env.example .env
        Write-Host ".env file created. You can edit it to configure settings." -ForegroundColor Green
    } else {
        Write-Host "Error: .env.example not found!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Starting Vite development server..." -ForegroundColor Green
Write-Host "Frontend will be available at http://localhost:5173" -ForegroundColor Green
Write-Host "Make sure the backend API is running on http://localhost:8000" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the dev server
npm run dev
