import { useRef, useState, useEffect } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { MovieCard, Movie } from "./MovieCard";

interface MovieRowProps {
  title: string;
  movies: Movie[];
  onRate: (movieId: number, rating: "up" | "down") => void;
  onDetails: (movie: Movie) => void;
  ratings: Record<number, "up" | "down">;
  emptyMessage?: string;
}

export function MovieRow({
  title,
  movies,
  onRate,
  onDetails,
  ratings,
  emptyMessage = "No movies in this category."
}: MovieRowProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);

  const checkScrollability = () => {
    if (!scrollContainerRef.current) return;
    
    const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;
    setShowLeftArrow(scrollLeft > 0);
    setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 10);
  };

  const handleScroll = () => {
    checkScrollability();
  };

  // Check scrollability when movies change or component mounts
  useEffect(() => {
    // Small delay to ensure DOM has updated
    const timer = setTimeout(() => {
      checkScrollability();
    }, 100);
    
    return () => clearTimeout(timer);
  }, [movies]);

  const scroll = (direction: "left" | "right") => {
    if (!scrollContainerRef.current) return;
    
    const container = scrollContainerRef.current;
    const scrollAmount = container.clientWidth * 0.8;
    const startPos = container.scrollLeft;
    const targetPos = direction === "left" 
      ? Math.max(0, startPos - scrollAmount)
      : Math.min(container.scrollWidth - container.clientWidth, startPos + scrollAmount);
    
    const distance = targetPos - startPos;
    const duration = 600; // milliseconds
    let startTime: number | null = null;

    const easeInOutCubic = (t: number): number => {
      return t < 0.5 
        ? 4 * t * t * t 
        : 1 - Math.pow(-2 * t + 2, 3) / 2;
    };

    const animateScroll = (currentTime: number) => {
      if (startTime === null) startTime = currentTime;
      const timeElapsed = currentTime - startTime;
      const progress = Math.min(timeElapsed / duration, 1);
      const easedProgress = easeInOutCubic(progress);
      
      container.scrollLeft = startPos + (distance * easedProgress);
      
      if (progress < 1) {
        requestAnimationFrame(animateScroll);
      }
    };

    requestAnimationFrame(animateScroll);
  };

  if (movies.length === 0) {
    return (
      <div>
        <h2 className="mb-4 text-[#F5C518] text-2xl font-bold">{title}</h2>
        <p className="text-gray-500 py-8">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="group/row">
      <h2 className="mb-4 text-[#F5C518] text-2xl font-bold">{title}</h2>
      <div className="relative">
        {/* Left Arrow - Desktop Only */}
        <button
          onClick={() => scroll("left")}
          className={`hidden md:flex absolute left-0 top-0 bottom-0 z-10 items-center justify-center w-32 bg-gradient-to-r from-[#121212] via-[#121212]/90 to-transparent transition-all ${
            showLeftArrow ? "opacity-90 hover:opacity-100" : "opacity-0 pointer-events-none"
          }`}
          aria-label="Scroll left"
        >
          <div className="w-28 h-28 rounded-full bg-[#F5C518] backdrop-blur-sm border-4 border-[#F5C518] flex items-center justify-center hover:bg-[#FFD54F] hover:border-[#FFD54F] hover:scale-110 active:scale-95 transition-all shadow-2xl shadow-[#F5C518]/20">
            <ChevronLeft className="w-16 h-16 text-black font-bold" strokeWidth={3} />
          </div>
        </button>

        {/* Scrollable Container */}
        <div
          ref={scrollContainerRef}
          onScroll={handleScroll}
          className="overflow-x-auto overflow-y-hidden pb-4 scrollbar-hide snap-x snap-mandatory md:snap-none"
          style={{
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
            scrollBehavior: 'smooth',
          }}
        >
          <div className="flex gap-3 md:gap-4 first:pl-0 last:pr-0">
            {movies.map((movie) => (
              <div
                key={movie.id}
                className="transition-all duration-300 ease-in-out flex-shrink-0 snap-start w-[45%] min-w-[160px] sm:w-[30%] md:w-[23%] lg:w-[18%] xl:w-[15%]"
              >
                <MovieCard
                  movie={movie}
                  onRate={onRate}
                  onDetails={onDetails}
                  rating={ratings[movie.id]}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Right Arrow - Desktop Only */}
        <button
          onClick={() => scroll("right")}
          className={`hidden md:flex absolute right-0 top-0 bottom-0 z-10 items-center justify-center w-32 bg-gradient-to-l from-[#121212] via-[#121212]/90 to-transparent transition-all ${
            showRightArrow ? "opacity-90 hover:opacity-100" : "opacity-0 pointer-events-none"
          }`}
          aria-label="Scroll right"
        >
          <div className="w-28 h-28 rounded-full bg-[#F5C518] backdrop-blur-sm border-4 border-[#F5C518] flex items-center justify-center hover:bg-[#FFD54F] hover:border-[#FFD54F] hover:scale-110 active:scale-95 transition-all shadow-2xl shadow-[#F5C518]/20">
            <ChevronRight className="w-16 h-16 text-black font-bold" strokeWidth={3} />
          </div>
        </button>
      </div>
    </div>
  );
}
