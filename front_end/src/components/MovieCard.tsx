import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";

export interface Movie {
  id: number;
  imdbID: string; // Full IMDb ID (e.g., tt0111161)
  title: string;
  year: number;
  genres: string[];
  description: string;
  fullDescription: string;
  imageUrl: string;
}

interface MovieCardProps {
  movie: Movie;
  onRate: (movieId: number, rating: "up" | "down") => void;
  onDetails: (movie: Movie) => void;
  rating?: "up" | "down" | null;
}

export function MovieCard({ movie, onRate, onDetails, rating }: MovieCardProps) {
  return (
    <Card 
      className="relative w-full overflow-hidden shadow-lg rounded-md bg-[#1a1a1a] border border-white/10 group cursor-pointer transition-transform duration-200 hover:scale-105" 
      style={{ aspectRatio: '2/3' }}
      onClick={() => onDetails(movie)}
    >
      {/* Background Image */}
      <img
        src={movie.imageUrl}
        alt={movie.title}
        className="w-full h-full object-cover absolute inset-0"
        onError={(e) => {
          e.currentTarget.src = 'https://via.placeholder.com/300x450?text=No+Poster';
        }}
      />
      
      {/* Hover Overlay - Desktop Only */}
      <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent opacity-0 md:group-hover:opacity-100 transition-opacity duration-300 p-3 flex flex-col justify-between">
        {/* Movie Info */}
        <div className="space-y-2 overflow-hidden">
          <h3 className="text-[#F5C518] font-bold line-clamp-2">{movie.title}</h3>
          <div className="flex flex-wrap gap-1">
            {movie.genres.slice(0, 2).map((genre) => (
              <Badge
                key={genre}
                variant="secondary"
                className="rounded-sm px-2 py-0.5 text-xs bg-[#F5C518]/20 text-[#F5C518] border-[#F5C518]/30"
              >
                {genre}
              </Badge>
            ))}
          </div>
          <p className="text-white text-xs line-clamp-3">{movie.description}</p>
        </div>

        {/* Buttons - Desktop Only */}
        <div className="hidden md:flex flex-col gap-2">
          <div className="flex gap-2">
            <Button
              variant={rating === "up" ? "default" : "outline"}
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onRate(movie.id, "up");
              }}
              className={`flex-1 h-8 px-2 ${
                rating === "up" 
                  ? "bg-[#F5C518] hover:bg-[#F5C518]/90 text-black" 
                  : "bg-white/10 text-white border-white/20 hover:bg-white/20"
              }`}
            >
              <ThumbsUp className="w-3 h-3" />
            </Button>
            <Button
              variant={rating === "down" ? "default" : "outline"}
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onRate(movie.id, "down");
              }}
              className={`flex-1 h-8 px-2 ${
                rating === "down" 
                  ? "bg-red-600 hover:bg-red-700 text-white" 
                  : "bg-white/10 text-white border-white/20 hover:bg-white/20"
              }`}
            >
              <ThumbsDown className="w-3 h-3" />
            </Button>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onDetails(movie);
            }}
            className="w-full h-8 text-xs bg-white/10 text-white border-white/20 hover:bg-white/20"
          >
            Details
          </Button>
        </div>
      </div>
    </Card>
  );
}
