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

  // Agrupar MULTICCU + AGUAS_DANONE en un solo slide
  const slides: { key: string; categories: CategoryKey[] }[] = [];
  if ('CERVEZAS' in categories) {
    slides.push({ key: 'CERVEZAS', categories: ['CERVEZAS'] });
  }
  const otros: CategoryKey[] = (['MULTICCU', 'AGUAS_DANONE'] as CategoryKey[]).filter(
    (k) => k in categories
  );
  if (otros.length > 0) {
    slides.push({ key: 'OTROS', categories: otros });
  }

  return (
    <div>
      <div ref={trackRef} className="carousel-track" onScroll={handleScroll}>
        {slides.map((slide) => (
          <div key={slide.key} className="carousel-slide">
            {slide.categories.map((key) => (
              <CategorySlide
                key={key}
                categoryKey={key}
                data={categories[key]}
              />
            ))}
          </div>
        ))}
      </div>
      {/* Dots */}
      {slides.length > 1 && (
        <div className="flex justify-center gap-2 py-2">
          {slides.map((slide, i) => (
            <button
              key={slide.key}
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
