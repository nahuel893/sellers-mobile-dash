import { useRef, useEffect, useState, useCallback } from 'react';
import type { CategoryData } from '../types/api';
import { CATEGORIES, type CategoryKey } from '../lib/constants';
import CategorySlide from './CategorySlide';

interface CategoryCarouselProps {
  categories: Record<string, CategoryData>;
  /** Índice de slide controlado externamente (CategoryToggle) */
  globalSlideIndex?: number;
}

export default function CategoryCarousel({
  categories,
  globalSlideIndex,
}: CategoryCarouselProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  // Sync con globalSlideIndex
  useEffect(() => {
    if (globalSlideIndex == null || !trackRef.current) return;
    const track = trackRef.current;
    const slideWidth = track.offsetWidth;
    track.scrollTo({ left: globalSlideIndex * slideWidth, behavior: 'smooth' });
  }, [globalSlideIndex]);

  // Trackear slide activo con scroll
  const handleScroll = useCallback(() => {
    if (!trackRef.current) return;
    const track = trackRef.current;
    const slideWidth = track.offsetWidth;
    if (slideWidth === 0) return;
    const index = Math.round(track.scrollLeft / slideWidth);
    setActiveIndex(index);
  }, []);

  // Click en dot
  const goToSlide = (index: number) => {
    if (!trackRef.current) return;
    const slideWidth = trackRef.current.offsetWidth;
    trackRef.current.scrollTo({ left: index * slideWidth, behavior: 'smooth' });
  };

  const categoryKeys = CATEGORIES.filter((key) => key in categories);

  return (
    <div>
      <div ref={trackRef} className="carousel-track" onScroll={handleScroll}>
        {categoryKeys.map((key) => (
          <div key={key} className="carousel-slide">
            <CategorySlide
              categoryKey={key as CategoryKey}
              data={categories[key]}
            />
          </div>
        ))}
      </div>
      {/* Dots */}
      {categoryKeys.length > 1 && (
        <div className="flex justify-center gap-2 py-2">
          {categoryKeys.map((key, i) => (
            <button
              key={key}
              onClick={() => goToSlide(i)}
              className={`w-2 h-2 rounded-full transition-all ${
                i === activeIndex
                  ? 'bg-brand-dark scale-125'
                  : 'bg-gray-300 hover:bg-gray-400'
              }`}
              aria-label={`Slide ${i + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
