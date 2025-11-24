// API configuration
// Only allow localhost:8000 for local development or the configured Render backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Debug: Log the API base URL being used
console.log('🔧 API_BASE_URL configured as:', API_BASE_URL);
console.log('🔧 VITE_API_BASE_URL from env:', import.meta.env.VITE_API_BASE_URL);

export interface OMDbMovieDetail {
  imdbID: string;
  Title: string;
  Year: string;
  Rated?: string;
  Released?: string;
  Runtime?: string;
  Genre?: string;
  Director?: string;
  Writer?: string;
  Actors?: string;
  Plot?: string;
  Language?: string;
  Country?: string;
  Awards?: string;
  Poster?: string;
  Ratings?: Array<{ Source: string; Value: string }>;
  Metascore?: string;
  imdbRating?: string;
  imdbVotes?: string;
  Type?: string;
  DVD?: string;
  BoxOffice?: string;
  Production?: string;
  Website?: string;
}

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

/**
 * Check API health and configuration
 */
export async function checkApiHealth(): Promise<ApiResponse<{ status: string; omdb_api_configured: boolean }>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    
    if (!response.ok) {
      return { error: 'API health check failed' };
    }
    
    const data = await response.json();
    return { data };
  } catch (error) {
    console.error('Error checking API health:', error);
    return { error: 'Network error occurred during health check' };
  }
}

/**
 * Get initial movie recommendations (top-rated movies)
 */
export async function getInitialRecommendations(
  limit: number = 20
): Promise<ApiResponse<OMDbMovieDetail[]>> {
  try {
    const params = new URLSearchParams({ limit: limit.toString() });
    const url = `${API_BASE_URL}/api/recommendations/initial?${params}`;
    console.log('🌐 Fetching initial recommendations from:', url);
    const response = await fetch(url);
    
    if (!response.ok) {
      const errorData = await response.json();
      return { error: errorData.detail || 'Failed to fetch initial recommendations' };
    }
    
    const data = await response.json();
    return { data };
  } catch (error) {
    console.error('Error fetching initial recommendations:', error);
    return { error: 'Network error occurred while fetching recommendations' };
  }
}

export interface UserPreference {
  imdb_id: string;
  rating: number; // 1.0 for like, 0.0 for dislike
}

/**
 * Get personalized recommendations based on user preferences
 */
export async function getRecommendationsFromPreferences(
  preferences: UserPreference[],
  limit: number = 20
): Promise<ApiResponse<OMDbMovieDetail[]>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/recommendations/user-preferences`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        preferences,
        limit,
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      return { error: errorData.detail || 'Failed to fetch personalized recommendations' };
    }
    
    const data = await response.json();
    return { data };
  } catch (error) {
    console.error('Error fetching personalized recommendations:', error);
    return { error: 'Network error occurred while fetching recommendations' };
  }
}

/**
 * Add a single preference and get updated recommendations
 */
export async function addPreferenceAndGetRecommendations(
  imdbId: string,
  rating: number,
  allPreferences: UserPreference[],
  limit: number = 20
): Promise<ApiResponse<OMDbMovieDetail[]>> {
  // Add the new preference to the list
  const updatedPreferences = [...allPreferences, { imdb_id: imdbId, rating }];
  
  // Get new recommendations with all preferences
  return getRecommendationsFromPreferences(updatedPreferences, limit);
}

/**
 * Get recommendations similar to a specific movie
 */
export async function getSimilarMovies(
  imdbId: string,
  limit: number = 10
): Promise<ApiResponse<OMDbMovieDetail[]>> {
  try {
    const params = new URLSearchParams({ limit: limit.toString() });
    const url = `${API_BASE_URL}/api/recommendations/similar/${imdbId}?${params}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      const errorData = await response.json();
      return { error: errorData.detail || 'Failed to fetch similar movies' };
    }
    
    const data = await response.json();
    return { data };
  } catch (error) {
    console.error('Error fetching similar movies:', error);
    return { error: 'Network error occurred while fetching similar movies' };
  }
}

/**
 * Search for movies by text query using embedding model
 */
export async function searchMoviesByQuery(
  query: string,
  limit: number = 25
): Promise<ApiResponse<OMDbMovieDetail[]>> {
  try {
    const params = new URLSearchParams({ 
      query: query,
      limit: limit.toString() 
    });
    const url = `${API_BASE_URL}/api/recommendations/knn?${params}`;
    console.log('🔍 Searching movies with query:', query);
    const response = await fetch(url);
    
    if (!response.ok) {
      const errorData = await response.json();
      return { error: errorData.detail || 'Failed to search movies' };
    }
    
    const data = await response.json();
    return { data };
  } catch (error) {
    console.error('Error searching movies:', error);
    return { error: 'Network error occurred while searching movies' };
  }
}
