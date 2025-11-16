# Movie Recommender Backend Start Script
# This script activates the virtual environment and starts the FastAPI server

Write-Host "Starting Movie Recommender Backend..." -ForegroundColor Cyan

# Check if virtual environment exists
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment not found. Creating one..." -ForegroundColor Yellow
    python -m venv venv
    & .\venv\Scripts\Activate.ps1
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Check if .env file exists
if (-not (Test-Path ".\.env")) {
    Write-Host "Warning: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and add your OMDb API key" -ForegroundColor Yellow
    Write-Host "Run: Copy-Item .env.example .env" -ForegroundColor Yellow
    exit 1
}

# Load environment variables from .env file
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Item -Path "env:$name" -Value $value
    }
}

# Check if OMDB_API_KEY is set
if (-not $env:OMDB_API_KEY -or $env:OMDB_API_KEY -eq "your_api_key_here") {
    Write-Host "Warning: OMDB_API_KEY not configured in .env file!" -ForegroundColor Red
    Write-Host "The API will run but OMDb endpoints will not work." -ForegroundColor Yellow
}

Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "API documentation available at http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
