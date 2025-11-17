from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import numpy as np
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv
from knn_recommender import get_recommender
from user_preferences import UserPreferences

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Movie Recommender API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000",
        "https://*.vercel.app",  # Allow Vercel deployments
        "https://*.netlify.app",  # Allow Netlify deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API key from environment variable
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

# Initialize paths for KNN recommender
RATINGS_FILE = DATA_DIR / "ratings_binary_genres_tfidf.csv"
LINKS_FILE = DATA_DIR / "links.csv"
MOVIES_FILE = DATA_DIR / "movies.csv"

# Initialize KNN recommender on startup
recommender = None
user_preferences_manager = None
cached_initial_recommendations = None  # Cache for initial recommendations

@app.on_event("startup")
async def startup_event():
    """Initialize the KNN recommender on application startup"""
    global recommender, user_preferences_manager, cached_initial_recommendations
    try:
        if RATINGS_FILE.exists() and LINKS_FILE.exists():
            print("Initializing KNN recommender...")
            recommender = get_recommender(
                data_path=str(RATINGS_FILE),
                links_file=str(LINKS_FILE),
                movies_file=str(MOVIES_FILE) if MOVIES_FILE.exists() else None,
                omdb_api_key=OMDB_API_KEY,
                k=100
            )
            print("KNN recommender initialized successfully!")
            
            # Initialize UserPreferences manager
            print("Initializing UserPreferences manager...")
            user_preferences_manager = UserPreferences(
                genre_columns=recommender.genre_columns,
                movies_path=str(MOVIES_FILE),
                links_path=str(LINKS_FILE)
            )
            print("UserPreferences manager initialized successfully!")
            
            # Precompute initial recommendations
            print("Precomputing initial recommendations...")
            mean_genre_vector = recommender.compute_mean_genre_vector()
            cached_initial_recommendations = await recommender.recommend_movies_with_details(
                genre_features=mean_genre_vector,
                limit=25
            )
            print(f"Initial recommendations precomputed: {len(cached_initial_recommendations)} movies cached")
        else:
            print(f"Warning: Data files not found in {DATA_DIR}")
            print(f"  - ratings_binary_genres_tfidf.csv exists: {RATINGS_FILE.exists()}")
            print(f"  - links.csv exists: {LINKS_FILE.exists()}")
            print("KNN recommendations will not be available.")
    except Exception as e:
        print(f"Error initializing KNN recommender: {e}")
        print("KNN recommendations will not be available.")



class MovieDetail(BaseModel):
    imdbID: str
    Title: str
    Year: str
    Rated: Optional[str]
    Released: Optional[str]
    Runtime: Optional[str]
    Genre: Optional[str]
    Director: Optional[str]
    Writer: Optional[str]
    Actors: Optional[str]
    Plot: Optional[str]
    Language: Optional[str]
    Country: Optional[str]
    Awards: Optional[str]
    Poster: Optional[str]
    Ratings: Optional[List[dict]]
    Metascore: Optional[str]
    imdbRating: Optional[str]
    imdbVotes: Optional[str]
    Type: Optional[str]
    DVD: Optional[str]
    BoxOffice: Optional[str]
    Production: Optional[str]
    Website: Optional[str]

class UserPreferenceInput(BaseModel):
    imdb_id: str
    rating: float  # 1.0 for like, 0.0 for dislike

class RecommendationRequest(BaseModel):
    preferences: List[UserPreferenceInput]
    limit: int = 20

@app.get("/")
async def root():
    return {
        "message": "Movie Recommender API",
        "status": "running",
        "omdb_configured": bool(OMDB_API_KEY)
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "omdb_api_configured": bool(OMDB_API_KEY),
        "knn_recommender_ready": recommender is not None
    }

@app.get("/api/movie/{imdb_id}")
async def get_movie_details(imdb_id: str, plot: str = "short"):
    """
    Get detailed information about a specific movie by IMDb ID
    
    Args:
        imdb_id: IMDb ID of the movie (e.g., tt1234567)
        plot: Plot length (short or full)
    """
    if not OMDB_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OMDb API key not configured. Please set OMDB_API_KEY environment variable."
        )
    
    try:
        params = {
            "apikey": OMDB_API_KEY,
            "i": imdb_id,
            "plot": plot
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://www.omdbapi.com/", params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("Response") == "False":
                raise HTTPException(status_code=404, detail=data.get("Error", "Movie not found"))
            
            return data
    
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from OMDb API: {str(e)}")

@app.get("/api/movie-by-title/{title}")
async def get_movie_by_title(title: str, year: Optional[int] = None, plot: str = "short"):
    """
    Get detailed information about a movie by title
    
    Args:
        title: Movie title
        year: Year of release (optional)
        plot: Plot length (short or full)
    """
    if not OMDB_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OMDb API key not configured. Please set OMDB_API_KEY environment variable."
        )
    
    try:
        params = {
            "apikey": OMDB_API_KEY,
            "t": title,
            "plot": plot
        }
        
        if year:
            params["y"] = str(year)
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://www.omdbapi.com/", params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("Response") == "False":
                raise HTTPException(status_code=404, detail=data.get("Error", "Movie not found"))
            
            return data
    
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from OMDb API: {str(e)}")

@app.get("/api/recommendations/initial")
async def get_initial_recommendations(limit: int = 20):
    """
    Get initial movie recommendations from precomputed cache
    
    Args:
        limit: Maximum number of movies to return (default: 20)
    
    Returns:
        List of movie details for recommended movies
    """
    if recommender is None:
        raise HTTPException(
            status_code=503,
            detail="KNN recommender not available. Data files may be missing."
        )
    
    if cached_initial_recommendations is None:
        raise HTTPException(
            status_code=503,
            detail="Initial recommendations not yet computed. Please try again shortly."
        )
    
    try:
        # Return cached recommendations, truncated to requested limit
        recommendations = cached_initial_recommendations[:limit]
        
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail="No recommendations found"
            )
        
        return recommendations
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving initial recommendations: {str(e)}"
        )

@app.get("/api/recommendations/knn")
async def get_knn_recommendations(genres: str, limit: int = 25):
    """
    Get movie recommendations using KNN based on genre preferences
    
    Args:
        genres: Comma-separated list of genres (e.g., "Action,Sci-Fi,Adventure")
        limit: Maximum number of movies to return (default: 20)
    
    Returns:
        List of movie details for recommended movies
    """
    if recommender is None:
        raise HTTPException(
            status_code=503,
            detail="KNN recommender not available. Data files may be missing."
        )
    
    if not OMDB_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OMDb API key not configured. Please set OMDB_API_KEY environment variable."
        )
    
    try:
        # Parse genres from comma-separated string
        liked_genres = [g.strip() for g in genres.split(",") if g.strip()]
        
        if not liked_genres:
            raise HTTPException(
                status_code=400,
                detail="At least one genre must be provided"
            )
        
        # Create a query vector based on genres
        query_vector = np.zeros(len(recommender.genre_columns), dtype=np.float32)
        
        for i, col in enumerate(recommender.genre_columns):
            genre_name = col.replace('genre_', '')
            if genre_name in liked_genres:
                query_vector[i] = 1.0
        
        # Normalize the vector
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm
        
        # Get recommendations
        recommendations = await recommender.recommend_movies_with_details(
            genre_features=query_vector,
            limit=limit
        )
        
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail="No recommendations found for the given genres"
            )
        
        return recommendations
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )

@app.get("/api/genres")
async def get_available_genres():
    """
    Get list of available genres for KNN recommendations
    
    Returns:
        List of genre names
    """
    if recommender is None:
        raise HTTPException(
            status_code=503,
            detail="KNN recommender not available. Data files may be missing."
        )
    
    try:
        # Extract genre names from genre columns
        genres = [col.replace('genre_', '') for col in recommender.genre_columns]
        return {"genres": sorted(genres)}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving genres: {str(e)}"
        )

@app.post("/api/recommendations/user-preferences")
async def get_recommendations_from_user_preferences(request: RecommendationRequest):
    """
    Get movie recommendations based on user preferences (liked/disliked movies)
    
    Args:
        request: RecommendationRequest containing list of preferences and limit
    
    Returns:
        List of movie details for recommended movies
    """
    if recommender is None or user_preferences_manager is None:
        raise HTTPException(
            status_code=503,
            detail="KNN recommender not available. Data files may be missing."
        )
    
    if not OMDB_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OMDb API key not configured. Please set OMDB_API_KEY environment variable."
        )
    
    try:
        # Clear previous preferences
        user_preferences_manager.preferences = {}
        user_preferences_manager.genre_vectors = {}
        
        # Add user preferences
        for pref in request.preferences:
            try:
                user_preferences_manager.add_preference(
                    imdb_id=pref.imdb_id,
                    rating=pref.rating
                )
            except ValueError as e:
                print(f"Warning: Could not add preference for {pref.imdb_id}: {e}")
                continue
        
        if not user_preferences_manager.preferences:
            raise HTTPException(
                status_code=400,
                detail="No valid preferences were provided"
            )
        
        # Compute query vector
        query_vector = user_preferences_manager.compute_query_vector()
        
        # Get recommendations using the query vector
        recommendations = await recommender.recommend_movies_with_details(
            genre_features=query_vector,
            limit=request.limit
        )
        
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail="No recommendations found for the given preferences"
            )
        
        return recommendations
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
