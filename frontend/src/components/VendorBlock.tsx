import { Link } from 'react-router';
import type { VendedorListItem } from '../types/api';
import CategoryCarousel from './CategoryCarousel';
import { toSlug } from '../lib/format';

interface VendorBlockProps {
  vendedor: VendedorListItem;
  globalSlideIndex?: number;
}

export default function VendorBlock({ vendedor, globalSlideIndex }: VendorBlockProps) {
  const pct = vendedor.categories.CERVEZAS?.resumen.pct_tendencia ?? 0;
  const anchorId = `vendor-${toSlug(vendedor.nombre).toLowerCase()}`;

  return (
    <div
      id={anchorId}
      className="border-t border-gray-200 mt-3 mx-2 scroll-mt-[200px]"
    >
      <div className="flex items-baseline gap-2 px-3 pt-3">
        <Link
          to={`/vendedor/${vendedor.slug}`}
          className="text-sm font-bold text-brand-dark hover:underline no-underline"
        >
          {vendedor.nombre}
        </Link>
        <span className="text-xs text-gray-400 font-medium">
          {pct.toFixed(1)}%
        </span>
      </div>
      <CategoryCarousel categories={vendedor.categories} globalSlideIndex={globalSlideIndex} />
    </div>
  );
}
