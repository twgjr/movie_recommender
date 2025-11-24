"""
KNN Movie Recommendation System using FAISS

This module implements a KNN-based movie recommender using semantic embeddings
from the all-MiniLM-L6-v2 model. It uses FAISS for efficient similarity search and
integrates with OMDb API for displaying movie details.
"""

import pandas as pd
import numpy as np
import faiss
import os
from typing import List, Dict, Optional
import httpx
from sentence_transformers import SentenceTransformer


class KNNMovieRecommender:
    """
    KNN-based movie recommender using FAISS for similarity search with semantic embeddings
    """
    
    def __init__(self, data_path: str, omdb_api_key: str = "", k: int = 100):
        self.data_path = data_path
        self.omdb_api_key = omdb_api_key
        self.k = k
        self.index = None
        self.movies_df = None
        self.embeddings = None
        self.embedding_model = None
        self.imdb_id_to_idx = {}  # Map IMDb ID to index in embeddings array
        
    def load_data(self, chunk_size: int = 100000):
        """
        Load the movies with embeddings dataset
        """
        # Read the CSV file with embeddings
        print("Loading movies with embeddings...")
        self.movies_df = pd.read_csv(self.data_path, low_memory=False)
        
        # Extract embedding columns (emb_0 through emb_383)
        embedding_cols = [col for col in self.movies_df.columns if col.startswith('emb_')]
        self.embeddings = self.movies_df[embedding_cols].values.astype(np.float32)
        
        # Create mapping from IMDb ID to index
        for idx, imdb_id in enumerate(self.movies_df['imdb_id'].values):
            # Format IMDb ID to match OMDB format (tt followed by 7 digits)
            formatted_id = f"tt{str(int(imdb_id)).zfill(7)}"
            self.imdb_id_to_idx[formatted_id] = idx
        
        print(f"Loaded {len(self.movies_df)} movies with {self.embeddings.shape[1]}-dimensional embeddings")
    
    def load_embedding_model(self):
        """
        Load the sentence transformer model for generating query embeddings
        """
        print("Loading embedding model: all-MiniLM-L6-v2...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print(f"Model loaded. Embedding dimension: {self.embedding_model.get_sentence_embedding_dimension()}")
    
    def create_query_embedding(self, text: str) -> np.ndarray:
        """
        Create an embedding for a query text using the same model as preprocessing
        """
        if self.embedding_model is None:
            self.load_embedding_model()
        
        embedding = self.embedding_model.encode(text, show_progress_bar=False)
        return embedding.astype(np.float32)
    
    def compute_mean_embedding(self) -> np.ndarray:
        """
        Compute the mean embedding across all movies in the database
        This represents the "average" movie and provides a neutral starting point
        """
        return np.mean(self.embeddings, axis=0).astype(np.float32)
    
    def compute_weighted_embedding_from_preferences(
        self, 
        liked_imdb_ids: List[str], 
        disliked_imdb_ids: List[str]
    ) -> Optional[np.ndarray]:
        """
        Compute a weighted embedding based on user preferences:
        - Add embeddings for liked movies
        - Subtract embeddings for disliked movies
        - Divide by total number of ratings
        
        Args:
            liked_imdb_ids: List of IMDb IDs for liked movies
            disliked_imdb_ids: List of IMDb IDs for disliked movies
            
        Returns:
            Weighted embedding vector or None if no valid preferences
        """
        liked_embeddings = []
        disliked_embeddings = []
        
        # Collect embeddings for liked movies
        for imdb_id in liked_imdb_ids:
            if imdb_id in self.imdb_id_to_idx:
                idx = self.imdb_id_to_idx[imdb_id]
                liked_embeddings.append(self.embeddings[idx])
        
        # Collect embeddings for disliked movies
        for imdb_id in disliked_imdb_ids:
            if imdb_id in self.imdb_id_to_idx:
                idx = self.imdb_id_to_idx[imdb_id]
                disliked_embeddings.append(self.embeddings[idx])
        
        # Need at least one preference
        total_count = len(liked_embeddings) + len(disliked_embeddings)
        if total_count == 0:
            return None
        
        # Calculate weighted sum: likes + dislikes (as negative contribution)
        weighted_sum = np.zeros_like(self.embeddings[0])
        
        if liked_embeddings:
            weighted_sum += np.sum(liked_embeddings, axis=0)
        
        if disliked_embeddings:
            weighted_sum -= np.sum(disliked_embeddings, axis=0)
        
        # Divide by total count to get the mean
        weighted_embedding = weighted_sum / total_count
        
        return weighted_embedding.astype(np.float32)

    def build_index(self):
        """Build FAISS index for efficient similarity search"""
        
        dimension = self.embeddings.shape[1]
        
        # Create a FAISS index using L2 (Euclidean) distance
        self.index = faiss.IndexFlatL2(dimension)
        
        # Add embedding vectors to the index
        self.index.add(self.embeddings)
        
        print(f"FAISS index built with {self.index.ntotal} vectors")
        
    def load_movielens_to_imdb_mapping(self, links_file: str, movies_file: Optional[str] = None):
        """
        This method is kept for backwards compatibility but is no longer needed
        since embeddings CSV already contains IMDb IDs and movie metadata
        """
        pass
        
    def get_similar_movies(self, query_embedding: np.ndarray, k: Optional[int] = None) -> List[str]:
        """
        Query the FAISS index to find k most similar movies based on embeddings
        
        Args:
            query_embedding: The query embedding vector
            k: Number of similar movies to return
            
        Returns:
            List of IMDb IDs for similar movies
        """
        if k is None:
            k = self.k
            
        # Ensure query vector is the right shape and type
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding.astype(np.float32)
        
        # Search the index
        distances, indices = self.index.search(query_embedding, k)

        # Get the IMDb IDs for the retrieved indices
        similar_movies = []
        for idx in indices[0]:
            imdb_id = self.movies_df.iloc[idx]['imdb_id']
            # Format as tt followed by 7 digits
            formatted_id = f"tt{str(int(imdb_id)).zfill(7)}"
            similar_movies.append(formatted_id)
        
        return similar_movies
    
    def get_local_movie_details(self, imdb_id: str) -> Optional[Dict]:
        """
        Get movie details from local movies_with_embeddings.csv
        """
        if self.movies_df is None:
            return None
        
        try:
            movie_row = self.movies_df[self.movies_df['imdb_id'] == int(imdb_id.replace('tt', ''))]
            
            if movie_row.empty:
                return None
            
            row = movie_row.iloc[0]
            
            # Create OMDb-like response with local data
            return {
                "imdbID": imdb_id,
                "Title": row['title'] if pd.notna(row['title']) else "N/A",
                "Year": row['year'] if pd.notna(row['year']) else "N/A",
                "Genre": row['genre'] if pd.notna(row['genre']) else "N/A",
                "Director": row['director'] if pd.notna(row['director']) else "N/A",
                "Actors": row['actors'] if pd.notna(row['actors']) else "N/A",
                "Plot": row['plot'] if pd.notna(row['plot']) else "N/A",
                "Poster": "N/A",
                "Type": "movie",
                "Response": "True",
                "imdbRating": row['imdb_rating'] if pd.notna(row['imdb_rating']) else "N/A",
                "Runtime": row['runtime'] if pd.notna(row['runtime']) else "N/A",
                "Rated": row['rated'] if pd.notna(row['rated']) else "N/A"
            }
        except Exception as e:
            print(f"Error getting local movie details for {imdb_id}: {str(e)}")
            return None
    
    async def get_movie_details_from_omdb(self, imdb_id: str) -> Optional[Dict]:
        """
        Fetch movie details from OMDb API, with fallback to local data
        """
        try:
            params = {
                "apikey": self.omdb_api_key,
                "i": imdb_id,
                "plot": "short"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get("http://www.omdbapi.com/", params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("Response") != "False":
                    return data
                else:
                    print(f"Movie not found in OMDb: {imdb_id}, trying local data")
                    return self.get_local_movie_details(imdb_id)
        
        except Exception as e:
            print(f"Error fetching movie {imdb_id} from OMDb: {str(e)}, trying local data")
            return self.get_local_movie_details(imdb_id)
    
    async def recommend_movies_with_details(
        self, 
        query_embedding: np.ndarray, 
        limit: int = 25
    ) -> List[Dict]:
        """
        Get movie recommendations with full details from OMDb or local data
        
        Args:
            query_embedding: The query embedding vector
            limit: Maximum number of recommendations to return
            
        Returns:
            List of movie dictionaries with details
        """
        # Get similar movie IMDb IDs
        imdb_movie_ids = self.get_similar_movies(query_embedding)
        
        # Fetch details
        movies_with_details = []
        
        for imdb_id in imdb_movie_ids:
            if len(movies_with_details) >= limit:
                break
            
            # Fetch details from OMDb or fall back to local data
            movie_details = await self.get_movie_details_from_omdb(str(imdb_id))
            if movie_details:
                movie_details['imdbId'] = imdb_id  # Add IMDb ID for reference
                movies_with_details.append(movie_details)
        
        return movies_with_details


# Singleton instance
_recommender_instance = None

def get_recommender(
    data_path: Optional[str] = None,
    links_file: Optional[str] = None,
    movies_file: Optional[str] = None,
    omdb_api_key: Optional[str] = None,
    k: int = 100,
    allow_no_api_key: bool = False
) -> KNNMovieRecommender:
    """
    Get or create the KNN recommender singleton instance
    """
    global _recommender_instance
    
    if _recommender_instance is None:
        if data_path is None:
            raise ValueError("data_path must be provided on first call to get_recommender()")
        
        # Get API key from environment if not provided
        if omdb_api_key is None:
            omdb_api_key = os.getenv("OMDB_API_KEY", "")
        
        if not omdb_api_key and not allow_no_api_key:
            raise ValueError("OMDb API key not configured. Set OMDB_API_KEY environment variable.")
        
        # Create and initialize recommender
        _recommender_instance = KNNMovieRecommender(data_path, omdb_api_key, k)
        _recommender_instance.load_data()
        _recommender_instance.load_embedding_model()
        _recommender_instance.build_index()
        # Links file kept for backwards compatibility but not needed with embeddings
        if links_file:
            _recommender_instance.load_movielens_to_imdb_mapping(links_file, movies_file)
    
    return _recommender_instance

async def main():
    """
    Example usage of the recommender with semantic embeddings
    """
    # Initialize recommender
    recommender = get_recommender(
        data_path=DATA_PATH,
        links_file=None,  # Not needed with embeddings CSV
        omdb_api_key=OMDB_API_KEY,
        k=100,
        allow_no_api_key=True  # Allow testing without API key
    )
    
    # Create a query based on movie preferences
    # For example, looking for movies similar to "action sci-fi thriller with AI"
    query_text = "Title: The Matrix. Genre: Action, Sci-Fi. Actors: Keanu Reeves. Plot: A hacker discovers reality is a simulation."
    
    # Generate query embedding
    query_embedding = recommender.create_query_embedding(query_text)
    
    # Get recommendations
    recommendations = await recommender.recommend_movies_with_details(
        query_embedding=query_embedding,
        limit=10
    )

    print("\nTop 10 Recommendations:")
    for i, movie in enumerate(recommendations, 1):
        print(f"{i}. {movie.get('Title')} ({movie.get('Year')})")
        print(f"   Genre: {movie.get('Genre')}")
        print(f"   IMDb ID: {movie.get('imdbID')}")
        print()

if __name__ == "__main__":
    # Example usage
    import asyncio
    
    # Configure paths (update these to your actual paths)
    DATA_PATH = "../model/movies_with_embeddings.csv"
    OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")
    
    asyncio.run(main())
