import type { CategoryData } from '../types/api';
import CategoryCarousel from './CategoryCarousel';

interface SummaryBlockProps {
  title: string;
  pctTendencia: number;
  categories: Record<string, CategoryData>;
  variant: 'sucursal' | 'supervisor';
  globalSlideIndex?: number;
}

export default function SummaryBlock({
  title,
  pctTendencia,
  categories,
  variant,
  globalSlideIndex,
}: SummaryBlockProps) {
  const isSucursal = variant === 'sucursal';
  const borderClass = isSucursal
    ? 'border-t-[3px] border-brand-dark bg-gradient-to-b from-white to-gray-50'
    : 'border-t-2 border-gray-300 bg-gradient-to-b from-gray-50 to-white';
  const titleClass = isSucursal
    ? 'text-base font-extrabold'
    : 'text-sm font-bold';

  return (
    <div className={`${borderClass} rounded-lg mt-3 mx-2 overflow-hidden`}>
      <div className="flex items-baseline gap-2 px-3 pt-3">
        <h3 className={`${titleClass} text-brand-dark`}>{title}</h3>
        <span className="text-xs text-gray-400 font-medium">
          {pctTendencia.toFixed(1)}%
        </span>
      </div>
      <CategoryCarousel categories={categories} globalSlideIndex={globalSlideIndex} />
    </div>
  );
}
