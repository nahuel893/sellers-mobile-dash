import { BrandCard } from './BrandCard';
import type { BrandCardProps } from './BrandCard';

interface BrandGridProps {
  cards: BrandCardProps[];
}

export function BrandGrid({ cards }: BrandGridProps) {
  if (cards.length === 0) {
    return (
      <p className="text-ink-3 text-sm py-8 text-center">
        Sin datos de marca para mostrar.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {cards.map((card) => (
        <BrandCard key={card.grupoMarca} {...card} />
      ))}
    </div>
  );
}
