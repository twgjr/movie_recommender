"""
Example: Using UserPreferences to Query KNN Recommender

This script demonstrates how to use UserPreferences to build a query vector
and get movie recommendations from the KNN recommender.
"""

import asyncio
import os
from user_preferences import UserPreferences
from knn_recommender import get_recommender


async def main():
    # Define genre columns (must match the columns in your data)
    genre_columns = [
        "genre_(no genres listed)", "genre_Action", "genre_Adventure",
        "genre_Animation", "genre_Children", "genre_Comedy", "genre_Crime",
        "genre_Documentary", "genre_Drama", "genre_Fantasy", "genre_Film-Noir",
        "genre_Horror", "genre_IMAX", "genre_Musical", "genre_Mystery",
        "genre_Romance", "genre_Sci-Fi", "genre_Thriller", "genre_War",
        "genre_Western"
    ]
    
    # Initialize UserPreferences
    print("Initializing UserPreferences...")
    user_prefs = UserPreferences(
        genre_columns=genre_columns,
        movies_path='data/movies.csv',
        links_path='data/links.csv'
    )
    
    # Add user preferences (IMDb IDs and ratings)
    print("\nAdding user preferences...")
    user_prefs.add_preference(imdb_id="0114746", rating=1.0)  # 12 Monkeys (Like)
    user_prefs.add_preference(imdb_id="0106977", rating=1.0)  # The Fugitive (Like)
    user_prefs.add_preference(imdb_id="0137523", rating=1.0)  # Fight Club (Like)
    user_prefs.add_preference(imdb_id="0102926", rating=0.0)  # The Silence of the Lambs (Dislike)
    
    print(f"Total preferences: {len(user_prefs.preferences)}")
    print(f"Liked movies: {sum(1 for r in user_prefs.preferences.values() if r > 0)}")
    print(f"Disliked movies: {sum(1 for r in user_prefs.preferences.values() if r == 0)}")
    
    # Compute query vector
    print("\nComputing query vector from preferences...")
    query_vector = user_prefs.compute_query_vector()
    print(f"Query vector shape: {query_vector.shape}")
    print(f"Query vector (first 5 values): {query_vector[:5]}")
    
    # Initialize KNN Recommender
    print("\nInitializing KNN Recommender...")
    omdb_api_key = os.getenv("OMDB_API_KEY", "")
    
    recommender = get_recommender(
        data_path='data/ratings_binary_genres_tfidf.csv',
        links_file='data/links.csv',
        omdb_api_key=omdb_api_key,
        k=100,
        allow_no_api_key=True  # Set to False if you want to require an API key
    )
    
    # Get recommendations using the query vector
    print("\nGetting recommendations based on user preferences...")
    recommendations = await recommender.recommend_from_user_preferences(
        query_vector=query_vector,
        limit=10
    )
    
    # Display recommendations
    print(f"\n{'='*70}")
    print(f"RECOMMENDED MOVIES (Based on Your Preferences)")
    print(f"{'='*70}")
    
    for i, movie in enumerate(recommendations, 1):
        print(f"\n{i}. {movie.get('Title', 'Unknown')} ({movie.get('Year', 'N/A')})")
        print(f"   IMDb ID: {movie.get('imdbID', 'N/A')}")
        print(f"   Genre: {movie.get('Genre', 'N/A')}")
        print(f"   IMDb Rating: {movie.get('imdbRating', 'N/A')}")
        print(f"   Plot: {movie.get('Plot', 'N/A')}")
    
    print(f"\n{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
