import { Dialog, DialogContent, DialogTitle, DialogDescription } from "./ui/dialog";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { Movie } from "./MovieCard";

interface DetailsModalProps {
  movie: Movie | null;
  open: boolean;
  onClose: () => void;
  onRate?: (movieId: number, rating: "up" | "down") => void;
  rating?: "up" | "down" | null;
}

export function DetailsModal({ movie, open, onClose, onRate, rating }: DetailsModalProps) {
  if (!movie) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-[#1a1a1a] border border-white/10">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Movie Poster */}
          <div className="flex-shrink-0 mx-auto md:mx-0">
            <img
              src={movie.imageUrl}
              alt={movie.title}
              className="w-48 h-72 object-cover rounded-md border border-white/10"
              onError={(e) => {
                e.currentTarget.src = 'https://via.placeholder.com/300x450?text=No+Poster';
              }}
            />
          </div>

          {/* Movie Details */}
          <div className="flex-1 space-y-4">
            {/* Title and Year */}
            <div>
              <DialogTitle className="mb-1 text-[#F5C518] text-2xl font-bold">{movie.title}</DialogTitle>
              <p className="text-gray-400">{movie.year}</p>
            </div>

            {/* Genres */}
            <div className="flex flex-wrap gap-2">
              {movie.genres.map((genre) => (
                <Badge
                  key={genre}
                  variant="secondary"
                  className="rounded-sm px-3 py-1 bg-[#F5C518]/20 text-[#F5C518] border-[#F5C518]/30"
                >
                  {genre}
                </Badge>
              ))}
            </div>

            {/* Full Description */}
            <DialogDescription asChild>
              <p className="text-gray-300 leading-relaxed">{movie.fullDescription}</p>
            </DialogDescription>

            {/* Rating Buttons */}
            {onRate && (
              <div className="flex gap-3 pt-4">
                <Button
                  variant={rating === "up" ? "default" : "outline"}
                  size="lg"
                  onClick={() => onRate(movie.id, "up")}
                  className={`flex-1 ${
                    rating === "up"
                      ? "bg-[#F5C518] hover:bg-[#F5C518]/90 text-black"
                      : "border-white/20 text-white hover:bg-white/10"
                  }`}
                >
                  <ThumbsUp className="w-5 h-5 mr-2" />
                  Like
                </Button>
                <Button
                  variant={rating === "down" ? "default" : "outline"}
                  size="lg"
                  onClick={() => onRate(movie.id, "down")}
                  className={`flex-1 ${
                    rating === "down"
                      ? "bg-red-600 hover:bg-red-700 text-white"
                      : "border-white/20 text-white hover:bg-white/10"
                  }`}
                >
                  <ThumbsDown className="w-5 h-5 mr-2" />
                  Dislike
                </Button>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
