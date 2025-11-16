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

2. **Deploy Backend:**
   - Railway → New Project → Deploy from GitHub
   - Select this repo
   - Set Root Directory: `back_end`
   - Add environment variable: `OMDB_API_KEY=<your-key>`
   - Copy the generated backend URL

3. **Deploy Frontend:**
   - Railway → Add Service → GitHub Repo
   - Select this repo again
   - Set Root Directory: `front_end`
   - Add environment variable: `VITE_API_BASE_URL=<your-backend-url>`
   - Deploy!

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
