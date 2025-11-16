"""
User Preferences Management

This module handles storing and managing user movie preferences (likes/dislikes)
and converting them into TF-IDF query vectors for recommendations.
"""

import numpy as np
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import ast
import pandas as pd

class UserPreferences:
    """
    Stores and manages user movie preferences with TF-IDF vectors
    """
    
    def __init__(self, 
                 genre_columns: List[str],
                 movies_path: str = 'data/movies.csv',
                 links_path: str = 'data/links.csv'
                                  ) -> None:
        """
        Initialize user preferences
        """
        self.preferences: dict[str, float] = {}
        self.genre_columns = genre_columns
        self.genre_vectors: dict[str, np.ndarray] = {}

        # load back_end\data\movies.csv
        self.movies_df = pd.read_csv(movies_path)

        # load back_end\data\links.csv links 
        links_df = pd.read_csv(links_path)

        # join movies_df and links_df on movieId
        self.movies_df = pd.merge(self.movies_df, links_df, on='movieId', how='left')

        # convert the genre columns from string representation of list to actual list
        self.movies_df['genres'] = self.movies_df['genres'].apply(lambda x: x.split('|') if isinstance(x, str) else [])

        # split the genre columns into separate columns with binary values
        for genre in self.genre_columns:
            self.movies_df[genre] = self.movies_df['genres'].apply(lambda x: 1 if genre.replace('genre_', '') in x else 0)

    def _get_genre_vector(self, imdb_id: str) -> np.ndarray:
        """
        Retrieve the genre multihot vector for a given IMDb ID
        """
        # Convert string imdb_id to int for comparison (removes leading zeros)
        imdb_id_int = int(imdb_id)
        movie_row = self.movies_df[self.movies_df['imdbId'] == imdb_id_int]
        
        if movie_row.empty:
            raise ValueError(f"IMDb ID {imdb_id} not found in movies dataset")
        genre_vector = movie_row[self.genre_columns].values.flatten()
        return genre_vector.astype(float)

    def add_preference(self, imdb_id: str,rating: float,) -> None:
        self.preferences[imdb_id] = rating
        self.genre_vectors[imdb_id] = self._get_genre_vector(imdb_id)
    
    def remove_preference(self, imdb_id: Any) -> bool:
        movie_key = str(imdb_id)
        if movie_key in self.preferences:
            del self.preferences[movie_key]
            del self.genre_vectors[movie_key]
            return True
        return False
    
    def compute_query_vector(self) -> np.ndarray:
        """
        Convert user preferences into a single TF-IDF query vector
        """
        if not self.preferences:
            raise ValueError("No user preferences to compute query vector")
        
        vector = np.zeros(len(self.genre_columns))
        
        for movie_key, rating in self.preferences.items():
            if rating > 0:
                vector += self.genre_vectors[movie_key]
            else:
                vector -= self.genre_vectors[movie_key]
        
        # apply tf-idf scaling (simple normalization here)
        total_prefs = len(self.preferences)
        if total_prefs > 0:
            vector /= total_prefs

        return vector

# Example usage
if __name__ == "__main__":
    genre_columns = [
        "genre_(no genres listed)","genre_Action","genre_Adventure",
        "genre_Animation","genre_Children","genre_Comedy","genre_Crime",
        "genre_Documentary","genre_Drama","genre_Fantasy","genre_Film-Noir",
        "genre_Horror","genre_IMAX","genre_Musical","genre_Mystery",
        "genre_Romance","genre_Sci-Fi","genre_Thriller","genre_War",
        "genre_Western"
    ]

    user_prefs = UserPreferences(genre_columns=genre_columns)
    twelve_monkeys_id = "0114746"
    user_prefs.add_preference(imdb_id=twelve_monkeys_id, rating=1.0)  # 12 Monkeys
    print(f"Added preference: imdb_id={twelve_monkeys_id}, rating={user_prefs.preferences[twelve_monkeys_id]}, genre_vector={user_prefs.genre_vectors[twelve_monkeys_id]}")
    fugitive_id = "0106977"
    user_prefs.add_preference(imdb_id=fugitive_id, rating=1.0)  # The Fugitive
    print(f"Added preference: imdb_id={fugitive_id}, rating={user_prefs.preferences[fugitive_id]}, genre_vector={user_prefs.genre_vectors[fugitive_id]}")
    silence_lambs_id = "0102926"
    user_prefs.add_preference(imdb_id=silence_lambs_id, rating=0.0)  # Silence of the Lambs (dislike)
    print(f"Added preference: imdb_id={silence_lambs_id}, rating={user_prefs.preferences[silence_lambs_id]}, genre_vector={user_prefs.genre_vectors[silence_lambs_id]}")
    
    query_vector = user_prefs.compute_query_vector()
    print("Computed Query Vector:", query_vector)
    print("Vector Shape:", query_vector.shape)
