from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import numpy as np
from typing import Optional, List, Dict
from pathlib import Path
from dotenv import load_dotenv
from knn_recommender import get_recommender

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Movie Recommender API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000",
        "http://localhost:3001",
        "https://movie-recommender-front-end.onrender.com",  # Your deployed frontend
        "https://*.vercel.app",  # Allow Vercel deployments
        "https://*.netlify.app",  # Allow Netlify deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API key from environment variable
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))

# Initialize paths for KNN recommender
EMBEDDINGS_FILE = DATA_DIR / "movies_with_embeddings.csv"

# Initialize KNN recommender on startup
recommender = None
cached_initial_recommendations = None  # Cache for initial recommendations

# Store user ratings: {imdb_id: rating} where rating is 1.0 (like) or 0.0 (dislike)
user_ratings: Dict[str, float] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the KNN recommender on application startup"""
    global recommender, cached_initial_recommendations
    try:
        if EMBEDDINGS_FILE.exists():
            print("Initializing KNN recommender with embeddings...")
            recommender = get_recommender(
                data_path=str(EMBEDDINGS_FILE),
                links_file=None,  # Not needed with embeddings
                movies_file=None,
                omdb_api_key=OMDB_API_KEY,
                k=100
            )
            print("KNN recommender initialized successfully!")
            
            # Precompute initial recommendations using mean of all embeddings
            print("Precomputing initial recommendations...")
            # Use the mean embedding to get a neutral, representative sample
            mean_embedding = recommender.compute_mean_embedding()
            cached_initial_recommendations = await recommender.recommend_movies_with_details(
                query_embedding=mean_embedding,
                limit=25
            )
            print(f"Initial recommendations precomputed: {len(cached_initial_recommendations)} movies cached")
        else:
            print(f"Warning: Embeddings file not found: {EMBEDDINGS_FILE}")
            print("KNN recommendations will not be available.")
    except Exception as e:
        print(f"Error initializing KNN recommender: {e}")
        import traceback
        traceback.print_exc()
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

class RatingSubmission(BaseModel):
    imdb_id: str
    rating: float  # 1.0 for like, 0.0 for dislike

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
async def get_knn_recommendations(query: str, limit: int = 25):
    """
    Get movie recommendations using KNN based on a text query
    
    Args:
        query: Text description of desired movie (e.g., "action sci-fi thriller with AI and robots")
        limit: Maximum number of movies to return (default: 25)
    
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
        if not query or not query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query text must be provided"
            )
        
        # Generate embedding for the query
        query_embedding = recommender.create_query_embedding(query)
        
        # Get recommendations
        recommendations = await recommender.recommend_movies_with_details(
            query_embedding=query_embedding,
            limit=limit
        )
        
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail="No recommendations found for the given query"
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
    Get list of unique genres from the movies database
    
    Returns:
        List of genre names
    """
    if recommender is None:
        raise HTTPException(
            status_code=503,
            detail="KNN recommender not available. Data files may be missing."
        )
    
    try:
        # Extract unique genres from the movies dataframe
        all_genres = set()
        for genres_str in recommender.movies_df['genre'].dropna():
            # Split by comma and add individual genres
            for genre in genres_str.split(','):
                genre = genre.strip()
                if genre and genre != 'N/A':
                    all_genres.add(genre)
        
        return {"genres": sorted(list(all_genres))}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving genres: {str(e)}"
        )

@app.post("/api/recommendations/user-preferences")
async def get_recommendations_from_user_preferences(request: RecommendationRequest):
    """
    Get movie recommendations based on user preferences (liked/disliked movies)
    Uses weighted embedding: (sum of liked embeddings - sum of disliked embeddings) / total count
    
    Args:
        request: RecommendationRequest containing list of preferences and limit
    
    Returns:
        List of movie details for recommended movies
    """
    global user_ratings
    
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
        if not request.preferences:
            raise HTTPException(
                status_code=400,
                detail="At least one preference must be provided"
            )
        
        # Update stored ratings with all preferences from request
        for pref in request.preferences:
            # Format IMDb ID to include 'tt' prefix if not present
            imdb_id = pref.imdb_id if pref.imdb_id.startswith('tt') else f"tt{pref.imdb_id.zfill(7)}"
            user_ratings[imdb_id] = pref.rating
            print(f"Stored rating: {imdb_id} = {pref.rating}")
        
        # Separate likes and dislikes
        liked_imdb_ids = [imdb_id for imdb_id, rating in user_ratings.items() if rating >= 0.5]
        disliked_imdb_ids = [imdb_id for imdb_id, rating in user_ratings.items() if rating < 0.5]
        
        print(f"Current ratings - Likes: {len(liked_imdb_ids)}, Dislikes: {len(disliked_imdb_ids)}")
        print(f"Liked movies: {liked_imdb_ids}")
        print(f"Disliked movies: {disliked_imdb_ids}")
        
        # Compute weighted embedding from preferences
        query_embedding = recommender.compute_weighted_embedding_from_preferences(
            liked_imdb_ids=liked_imdb_ids,
            disliked_imdb_ids=disliked_imdb_ids
        )
        
        if query_embedding is None:
            raise HTTPException(
                status_code=400,
                detail="Could not compute embedding from preferences. Please check IMDb IDs."
            )
        
        # Get recommendations
        recommendations = await recommender.recommend_movies_with_details(
            query_embedding=query_embedding,
            limit=request.limit + len(user_ratings)  # Get extra to account for filtering
        )
        
        # Filter out movies that were already rated
        rated_imdb_ids = set(user_ratings.keys())
        recommendations = [r for r in recommendations if r.get('imdbID') not in rated_imdb_ids]
        
        # Limit to requested amount
        recommendations = recommendations[:request.limit]
        
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail="No recommendations found for the given preferences"
            )
        
        print(f"Returning {len(recommendations)} recommendations")
        return recommendations
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )

@app.post("/api/ratings/submit")
async def submit_rating(rating: RatingSubmission):
    """
    Submit a single movie rating (like or dislike)
    
    Args:
        rating: RatingSubmission containing imdb_id and rating value
    
    Returns:
        Confirmation of stored rating
    """
    global user_ratings
    
    try:
        # Format IMDb ID to include 'tt' prefix if not present
        imdb_id = rating.imdb_id if rating.imdb_id.startswith('tt') else f"tt{rating.imdb_id.zfill(7)}"
        
        # Store the rating
        user_ratings[imdb_id] = rating.rating
        
        # Count current likes and dislikes
        likes = sum(1 for r in user_ratings.values() if r >= 0.5)
        dislikes = sum(1 for r in user_ratings.values() if r < 0.5)
        
        print(f"Rating stored: {imdb_id} = {rating.rating}")
        print(f"Total ratings: {len(user_ratings)} (Likes: {likes}, Dislikes: {dislikes})")
        
        return {
            "success": True,
            "imdb_id": imdb_id,
            "rating": rating.rating,
            "total_ratings": len(user_ratings),
            "likes": likes,
            "dislikes": dislikes
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error storing rating: {str(e)}"
        )

@app.get("/api/ratings/all")
async def get_all_ratings():
    """
    Get all stored user ratings
    
    Returns:
        Dictionary of all ratings with summary statistics
    """
    likes = {imdb_id: rating for imdb_id, rating in user_ratings.items() if rating >= 0.5}
    dislikes = {imdb_id: rating for imdb_id, rating in user_ratings.items() if rating < 0.5}
    
    return {
        "total_ratings": len(user_ratings),
        "likes": likes,
        "dislikes": dislikes,
        "like_count": len(likes),
        "dislike_count": len(dislikes)
    }

@app.delete("/api/ratings/clear")
async def clear_ratings():
    """
    Clear all stored user ratings (useful for testing)
    
    Returns:
        Confirmation of cleared ratings
    """
    global user_ratings
    count = len(user_ratings)
    user_ratings.clear()
    print(f"Cleared {count} ratings")
    return {"success": True, "cleared_count": count}

@app.get("/api/recommendations/similar/{imdb_id}")
async def get_similar_to_movie(imdb_id: str, limit: int = 10):
    """
    Get movie recommendations similar to a specific movie
    
    Args:
        imdb_id: IMDb ID of the movie (without 'tt' prefix)
        limit: Maximum number of movies to return (default: 10)
    
    Returns:
        List of movie details for similar movies
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
        # Format IMDb ID to include 'tt' prefix if not present
        formatted_imdb_id = imdb_id if imdb_id.startswith('tt') else f"tt{imdb_id.zfill(7)}"
        
        # Check if movie exists in our database
        if formatted_imdb_id not in recommender.imdb_id_to_idx:
            raise HTTPException(
                status_code=404,
                detail=f"Movie with IMDb ID {formatted_imdb_id} not found in database"
            )
        
        # Get the embedding for this movie
        movie_idx = recommender.imdb_id_to_idx[formatted_imdb_id]
        movie_embedding = recommender.embeddings[movie_idx]
        
        # Get recommendations based on this movie's embedding
        recommendations = await recommender.recommend_movies_with_details(
            query_embedding=movie_embedding,
            limit=limit + 1  # Get extra to exclude the source movie
        )
        
        # Filter out the source movie itself
        recommendations = [r for r in recommendations if r.get('imdbID') != formatted_imdb_id]
        
        # Limit to requested amount
        recommendations = recommendations[:limit]
        
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail="No similar movies found"
            )
        
        return recommendations
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error finding similar movies: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
