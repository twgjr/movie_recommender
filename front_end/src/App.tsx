import { useState, useEffect } from "react";
import { Movie } from "./components/MovieCard";
import { DetailsModal } from "./components/DetailsModal";
import { Button } from "./components/ui/button";
import { MovieRow } from "./components/MovieRow";
import { Input } from "./components/ui/input";
import { getInitialRecommendations, getRecommendationsFromPreferences, addPreferenceAndGetRecommendations, OMDbMovieDetail, UserPreference } from "./services/movieApi";
import { Loader2 } from "lucide-react";

// Helper function to convert OMDb movie to our Movie format
function convertOMDbToMovie(omdbMovie: OMDbMovieDetail): Movie {
  const genres = omdbMovie.Genre 
    ? omdbMovie.Genre.split(', ') 
    : ['Unknown'];
  
  const plot = omdbMovie.Plot 
    ? omdbMovie.Plot 
    : 'No description available.';

  return {
    id: parseInt(omdbMovie.imdbID.replace('tt', ''), 10),
    imdbID: omdbMovie.imdbID,
    title: omdbMovie.Title,
    year: parseInt(omdbMovie.Year.split('–')[0], 10),
    genres: genres,
    description: plot.length > 150 ? plot.substring(0, 150) + '...' : plot,
    fullDescription: plot,
    imageUrl: omdbMovie.Poster && omdbMovie.Poster !== 'N/A' ? omdbMovie.Poster : 'https://via.placeholder.com/300x450?text=No+Poster'
  };
}

type Screen = "recommendations" | "confirmation";

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>("recommendations");
  const [ratings, setRatings] = useState<Record<number, "up" | "down">>({});
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [movies, setMovies] = useState<Movie[]>([]);
  const [movieQuery, setMovieQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isUpdatingRecommendations, setIsUpdatingRecommendations] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch initial recommendations on mount
  useEffect(() => {
    const fetchInitialMovies = async () => {
      setIsLoading(true);
      setError(null);

      const result = await getInitialRecommendations(20);
      if (result.data) {
        const convertedMovies = result.data.map(convertOMDbToMovie);
        setMovies(convertedMovies);
      } else {
        setError(result.error || "Failed to fetch initial recommendations");
      }

      setIsLoading(false);
    };

    fetchInitialMovies();
  }, []); // Empty dependency array means this runs once on mount

  // Categorize movies
  const topRecommendations = movies.filter((movie) => !ratings[movie.id]);
  const likedMovies = movies.filter((movie) => ratings[movie.id] === "up");
  const dislikedMovies = movies.filter((movie) => ratings[movie.id] === "down");

  const handleRate = async (movieId: number, rating: "up" | "down") => {
    // Find the movie to get its IMDb ID
    const movie = movies.find(m => m.id === movieId);
    if (!movie) return;
    
    // Update local ratings state immediately for UI responsiveness
    setRatings((prev) => ({
      ...prev,
      [movieId]: rating,
    }));
    
    // Convert IMDb ID (remove 'tt' prefix for backend)
    const imdbIdWithoutPrefix = movie.imdbID.replace('tt', '');
    const ratingValue = rating === 'up' ? 1.0 : 0.0;
    
    // Get current preferences as UserPreference array
    const currentPreferences: UserPreference[] = Object.entries(ratings)
      .map(([id, rat]) => {
        const m = movies.find(movie => movie.id === parseInt(id));
        return m ? {
          imdb_id: m.imdbID.replace('tt', ''),
          rating: rat === 'up' ? 1.0 : 0.0
        } : null;
      })
      .filter((p): p is UserPreference => p !== null);
    
    // Fetch new recommendations based on updated preferences
    setIsUpdatingRecommendations(true);
    const result = await addPreferenceAndGetRecommendations(
      imdbIdWithoutPrefix,
      ratingValue,
      currentPreferences,
      20
    );
    
    if (result.data) {
      const newRecommendations = result.data.map(convertOMDbToMovie);
      
      // Replace top recommendations (unrated movies) with new recommendations
      setMovies(prevMovies => {
        // Keep rated movies
        const ratedMovies = prevMovies.filter(m => ratings[m.id] || m.id === movieId);
        
        // Filter out duplicates from new recommendations
        const uniqueNewRecs = newRecommendations.filter(
          newMovie => !ratedMovies.some(rated => rated.id === newMovie.id)
        );
        
        return [...ratedMovies, ...uniqueNewRecs];
      });
    } else if (result.error) {
      setError(result.error);
    }
    
    setIsUpdatingRecommendations(false);
  };

  const handleDetails = (movie: Movie) => {
    setSelectedMovie(movie);
    setModalOpen(true);
  };



  if (currentScreen === "confirmation") {
    return (
      <div className="min-h-screen bg-[#121212] flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-[#1a1a1a] rounded-lg shadow-xl border border-white/10 p-12 text-center space-y-4">
          <div className="w-16 h-16 bg-[#F5C518]/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg
              className="w-8 h-8 text-[#F5C518]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h1 className="text-[#F5C518]">Thanks! Your recommendations have been saved.</h1>
          <Button
            onClick={() => {
              setCurrentScreen("recommendations");
              setRatings({});
            }}
            className="mt-6 bg-[#F5C518] text-black hover:bg-[#F5C518]/90"
          >
            Rate More Movies
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#121212] relative">
      {/* Loading Overlay */}
      {isUpdatingRecommendations && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-[#1a1a1a] rounded-lg p-8 shadow-2xl border border-white/10 flex flex-col items-center gap-4">
            <Loader2 className="w-12 h-12 animate-spin text-[#F5C518]" />
            <p className="text-white text-lg font-medium">Updating recommendations...</p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-[#1a1a1a] border-b border-white/10 sticky top-0 z-10 shadow-lg">
        <div className="w-full px-6 py-4">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <h1 className="text-[#F5C518] text-2xl md:text-3xl font-bold">Movie Recommender</h1>
            </div>

            {/* Error Message */}
            {error && (
              <div className="text-sm text-red-500">
                ⚠️ {error}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Movie Lists */}
      <div className="w-full py-6 space-y-8 px-6 md:px-12">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#F5C518]" />
          </div>
        ) : (
          <>
            <MovieRow
              title="Top Recommendations"
              movies={topRecommendations}
              onRate={handleRate}
              onDetails={handleDetails}
              ratings={ratings}
              emptyMessage="No movies yet. Enter a movie title above to fetch from OMDb!"
            />
            
            <MovieRow
              title="Liked Movies"
              movies={likedMovies}
              onRate={handleRate}
              onDetails={handleDetails}
              ratings={ratings}
              emptyMessage="No likes yet. Give a thumbs up to movies you enjoy!"
            />
            
            <MovieRow
              title="Disliked Movies"
              movies={dislikedMovies}
              onRate={handleRate}
              onDetails={handleDetails}
              ratings={ratings}
              emptyMessage="No dislikes yet. Give a thumbs down to movies you don't enjoy."
            />
          </>
        )}
      </div>

      {/* Details Modal */}
      <DetailsModal
        movie={selectedMovie}
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onRate={handleRate}
        rating={selectedMovie ? ratings[selectedMovie.id] : undefined}
      />
    </div>
  );
}
