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
    ? 'border-t-[3px] border-ink-0 bg-bg-1'
    : 'border-t-2 border-line bg-bg-1';
  const titleClass = isSucursal
    ? 'text-base font-extrabold'
    : 'text-sm font-bold';

  return (
    <div className={`${borderClass} rounded-lg mt-3 mx-2 overflow-hidden`}>
      <div className="flex items-baseline gap-2 px-3 pt-3">
        <h3 className={`${titleClass} text-ink-0`}>{title}</h3>
        <span className="text-xs text-ink-2 font-mono font-medium">
          {pctTendencia.toFixed(1)}%
        </span>
      </div>
      <CategoryCarousel categories={categories} globalSlideIndex={globalSlideIndex} />
    </div>
  );
}
