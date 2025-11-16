# Movie Recommender System

An AI-powered movie recommendation system using KNN-based collaborative filtering with OMDb API integration.

## Project Structure

- `back_end/` - FastAPI backend with KNN recommender
- `front_end/` - React + TypeScript frontend with Vite

## Deployment on Railway

### Prerequisites
- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))
- OMDb API key (get from [omdbapi.com](https://www.omdbapi.com/apikey.aspx))

### Quick Deploy

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Deploy Backend Service:**
   - Go to Railway → New Project → Deploy from GitHub
   - Select this repository
   - Railway will detect the `start.sh` file
   - Add these environment variables:
     - `SERVICE=backend`
     - `OMDB_API_KEY=<your-omdb-api-key>`
   - The backend will be deployed at the generated Railway URL
   - Copy this URL for the frontend configuration

3. **Deploy Frontend Service:**
   - In the same Railway project → New Service → GitHub Repo
   - Select this repository again
   - Add these environment variables:
     - `SERVICE=frontend`
     - `VITE_API_BASE_URL=<your-backend-railway-url>`
   - The frontend will be deployed at a separate Railway URL

### Important Notes
- The `start.sh` script automatically detects which service to run based on the `SERVICE` environment variable
- Make sure both services are in the same Railway project for easier management
- The backend needs access to the `data/` folder with CSV files
- Set appropriate CORS origins in `back_end/main.py` if needed

## Local Development

### Backend
```bash
cd back_end
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd front_end
npm install
npm run dev
```

## Features
- KNN-based movie recommendations
- User preference learning (like/dislike)
- Rich movie details from OMDb
- Responsive UI with movie cards
- Real-time recommendation updates
