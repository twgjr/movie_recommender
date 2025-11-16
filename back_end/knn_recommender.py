"""
KNN Movie Recommendation System using FAISS

This module implements a KNN-based movie recommender using genre TF-IDF features
from the MovieLens dataset. It uses FAISS for efficient similarity search and
integrates with OMDb API for displaying movie details.
"""

import pandas as pd
import numpy as np
import faiss
import os
from typing import List, Dict, Optional
import httpx
import ast


class KNNMovieRecommender:
    """
    KNN-based movie recommender using FAISS for similarity search
    """
    
    def __init__(self, data_path: str, omdb_api_key: str = "", k: int = 100):
        self.data_path = data_path
        self.omdb_api_key = omdb_api_key
        self.k = k
        self.index = None
        self.genre_columns = []
        self.train_idx_to_movies = {}
        self.movie_id_to_imdb = {}  # Mapping from MovieLens ID to IMDb ID
        self.imdb_to_movie_id = {}  # Reverse mapping
        self.movies_df = None  # Local movie data for fallback
        
    def load_data(self, chunk_size: int = 100000):
        """
        Load the MovieLens training dataset
        """
        
        # Read the data in chunks due to large file size
        train_chunks = []
        for chunk in pd.read_csv(self.data_path, chunksize=chunk_size):
            train_chunks.append(chunk)
        
        train_data = pd.concat(train_chunks, ignore_index=True)
        
        # Identify genre columns
        self.genre_columns = [col for col in train_data.columns if col.startswith('genre_')]
        
        # Extract genre features
        X_train_dict = {}
        for col in self.genre_columns:
            X_train_dict[col] = train_data[col].values.astype(np.float32)
        self.X_train = np.column_stack([X_train_dict[col] for col in self.genre_columns]).astype(np.float32)

        # map training indices to MovieLens IDs
        # self.train_idx_to_movies = {}
        # for idx, movie_id in enumerate(train_data['movieId'].values):
        #     if idx not in self.train_idx_to_movies:
        #         self.train_idx_to_movies[idx] = []
        #     self.train_idx_to_movies[idx].append(movie_id)
        self.train_idx_to_movies = {}
        for row in train_data.itertuples():
            idx = row.Index
            movie_id_list = row.movieId # df has actually a list of movieIds

            # convert string representation of list to actual list
            movie_id_list = ast.literal_eval(str(movie_id_list))

            if type(movie_id_list) is not list:
                raise ValueError(f"Expected list of movieIds, got {type(movie_id_list)}: {movie_id_list}")

            self.train_idx_to_movies[idx] = movie_id_list
    
    def compute_mean_genre_vector(self) -> np.ndarray:
        """
        Compute the mean genre vector across all training data
        """
        return np.mean(self.X_train, axis=0).astype(np.float32)

    def build_index(self):
        """Build FAISS index for efficient similarity search"""
        
        dimension = self.X_train.shape[1]
        
        # Create a FAISS index using L2 (Euclidean) distance
        self.index = faiss.IndexFlatL2(dimension)
        
        # Add training vectors to the index
        self.index.add(self.X_train)
        
    def load_movielens_to_imdb_mapping(self, links_file: str, movies_file: Optional[str] = None):
        """
        Load mapping from MovieLens IDs to IMDb IDs and movie metadata
        """
        links_df = pd.read_csv(links_file)
        
        # Create mapping dictionary
        for _, row in links_df.iterrows():
            ml_id = int(row['movieId'])
            imdb_id = f"tt{int(row['imdbId']):07d}"  # Format as tt followed by 7-digit zero-padded number
            self.movie_id_to_imdb[ml_id] = imdb_id
            self.imdb_to_movie_id[imdb_id] = ml_id
        
        # Load movies data for fallback
        if movies_file:
            self.movies_df = pd.read_csv(movies_file)
            # Merge with links to have IMDb IDs
            self.movies_df = pd.merge(self.movies_df, links_df, on='movieId', how='left')
            self.movies_df['imdbID'] = self.movies_df['imdbId'].apply(
                lambda x: f"tt{int(x):07d}" if pd.notna(x) else None
            )
        
    def get_similar_movies(self, genre_features: np.ndarray, k: Optional[int] = None) -> List[int]:
        """
        Query the FAISS index to find k most similar movies based on genre features
        """
        if k is None:
            k = self.k
            
        # Ensure query vector is the right shape and type
        if genre_features.ndim == 1:
            genre_features = genre_features.reshape(1, -1)
        genre_features = genre_features.astype(np.float32)
        
        # Search the index
        distances, indices = self.index.search(genre_features, k)

        # Get the movie lists for the retrieved indices
        similar_movies = {}
        for idx in indices[0]:
            movies = self.train_idx_to_movies[idx]
            for movieId in movies:
                imdb_id = self.movie_id_to_imdb[movieId]
                if imdb_id not in similar_movies:
                    similar_movies[imdb_id] = 1
                else:
                    similar_movies[imdb_id] += 1

        # list of unique similar movies sorted by frequency descending 
        unique_similar_movies = sorted(similar_movies.keys(), key=lambda x: similar_movies[x], reverse=True)
        
        return unique_similar_movies
    
    def get_local_movie_details(self, imdb_id: str) -> Optional[Dict]:
        """
        Get movie details from local movies.csv as fallback
        """
        if self.movies_df is None:
            return None
        
        try:
            movie_row = self.movies_df[self.movies_df['imdbID'] == imdb_id]
            
            if movie_row.empty:
                return None
            
            row = movie_row.iloc[0]
            title_with_year = row['title']
            
            # Extract year from title (format: "Title (YYYY)")
            year = "N/A"
            title = title_with_year
            if '(' in title_with_year and ')' in title_with_year:
                parts = title_with_year.rsplit('(', 1)
                if len(parts) == 2:
                    title = parts[0].strip()
                    year = parts[1].replace(')', '').strip()
            
            # Create OMDb-like response with local data
            return {
                "imdbID": imdb_id,
                "Title": title,
                "Year": year,
                "Genre": row['genres'].replace('|', ', ') if pd.notna(row['genres']) else "N/A",
                "Plot": "Plot information not available from local data.",
                "Poster": "N/A",
                "Type": "movie",
                "Response": "True"
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
        genre_features: np.ndarray, 
        limit: int = 25
    ) -> List[Dict]:
        """
        Get movie recommendations with full details from OMDb
        """
        # Get similar MovieLens movie IDs
        imdb_movie_ids = self.get_similar_movies(genre_features)
        
        # Convert to IMDb IDs and fetch details
        movies_with_details = []
        
        for imdb_id in imdb_movie_ids:
            if len(movies_with_details) >= limit:
                break
            
            # Fetch details from OMDb
            movie_details = await self.get_movie_details_from_omdb(str(imdb_id))
            if movie_details:
                movie_details['imdbId'] = imdb_id  # Add Imdb ID for reference
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
        if links_file is None:
            raise ValueError("links_file must be provided on first call to get_recommender()")
        
        # Get API key from environment if not provided
        if omdb_api_key is None:
            omdb_api_key = os.getenv("OMDB_API_KEY", "")
        
        if not omdb_api_key and not allow_no_api_key:
            raise ValueError("OMDb API key not configured. Set OMDB_API_KEY environment variable.")
        
        # Create and initialize recommender
        _recommender_instance = KNNMovieRecommender(data_path, omdb_api_key, k)
        _recommender_instance.load_data()
        _recommender_instance.build_index()
        _recommender_instance.load_movielens_to_imdb_mapping(links_file, movies_file)
    
    return _recommender_instance

async def main():
    from user_preferences import UserPreferences
    
    # create a user preferences example
    user = UserPreferences(
        genre_columns=[col for col in pd.read_csv(DATA_PATH, nrows=1).columns if col.startswith('genre_')],
        movies_path='data/movies.csv',
        links_path='data/links.csv'
    )

    # Add some preferences (example IMDb IDs and ratings)
    user.add_preference('0114709', 0.0)  # Toy Story
    user.add_preference('0133093', 1.0)  # The Matrix
    user.add_preference('1375666', 1.0)  # Inception

    # Initialize recommender
    recommender = get_recommender(
        data_path=DATA_PATH,
        links_file=LINKS_FILE,
        omdb_api_key=OMDB_API_KEY,
        k=10
    )
    
    # get recommendations based on user preferences
    recommendations = recommender.recommend_movies_with_details(
        genre_features=user.compute_query_vector(),
        limit=25
    )

    recommended_movies = await recommendations
    for movie in recommended_movies:
        print(f"{movie.get('Title')} ({movie.get('Year')}), IMDb ID: {movie.get('imdbID')}")

if __name__ == "__main__":
    # Example usage
    import asyncio
    
    # Configure paths (update these to your actual paths)
    DATA_PATH = "data/ratings_binary_genres_tfidf.csv"
    LINKS_FILE = "data/links.csv"
    OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")
    
    asyncio.run(main())
