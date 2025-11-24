import { Dialog, DialogContent, DialogTitle, DialogDescription } from "./ui/dialog";
import { MovieCard, Movie } from "./MovieCard";

interface SearchResultsModalProps {
  movies: Movie[];
  open: boolean;
  onClose: () => void;
  onRate: (movieId: number, rating: "up" | "down") => void;
  onDetails: (movie: Movie) => void;
  ratings: Record<number, "up" | "down">;
  searchQuery: string;
}

export function SearchResultsModal({ 
  movies, 
  open, 
  onClose, 
  onRate, 
  onDetails, 
  ratings,
  searchQuery 
}: SearchResultsModalProps) {
  const handleRate = (movieId: number, rating: "up" | "down") => {
    onRate(movieId, rating);
    // Close modal after rating
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent 
        className="bg-[#1a1a1a] border border-white/10 p-0 gap-0"
        style={{ 
          maxWidth: '90vw', 
          width: '1200px',
          height: '80vh',
          maxHeight: '80vh',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Header */}
        <div className="flex-shrink-0 bg-[#1a1a1a] border-b border-white/10 p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <DialogTitle className="text-[#F5C518] text-2xl font-bold mb-1">
                Search Results
              </DialogTitle>
              <DialogDescription className="text-gray-400 text-sm">
                {movies.length} movies found for: <span className="text-white font-medium">"{searchQuery}"</span>
              </DialogDescription>
            </div>
          </div>
        </div>

        {/* Movie Grid - Scrollable */}
        <div 
          className="p-6"
          style={{ 
            flex: '1 1 0',
            overflowY: 'auto',
            overflowX: 'hidden',
            minHeight: 0
          }}
        >
          {movies.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              No movies found matching your search.
            </div>
          ) : (
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', 
              gap: '1.25rem' 
            }}>
              {movies.map((movie) => (
                <MovieCard
                  key={movie.id}
                  movie={movie}
                  onRate={handleRate}
                  onDetails={onDetails}
                  rating={ratings[movie.id]}
                />
              ))}
            </div>
          )}
        </div>

        {/* Footer hint */}
        <div className="flex-shrink-0 bg-[#1a1a1a] border-t border-white/10 px-4 py-2">
          <p className="text-xs text-gray-500 text-center">
            Click on a movie to see details, or rate it to add to your preferences
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
