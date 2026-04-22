
interface BrandStat {
  grupoMarca: string;
  pct: number;
}

interface StatsStripProps {
  brands: BrandStat[];
}

export function StatsStrip({ brands }: StatsStripProps) {
  const above = brands.filter((b) => b.pct > 60);
  const critical = brands.filter((b) => b.pct < 40);

  const sorted = [...brands].sort((a, b) => b.pct - a.pct);
  const best = sorted[0] ?? null;
  const worst = sorted[sorted.length - 1] ?? null;

  const aboveNames = above
    .slice(0, 3)
    .map((b) => b.grupoMarca)
    .join(', ');

  const critNames = critical
    .slice(0, 3)
    .map((b) => b.grupoMarca)
    .join(', ');

  const stats = [
    {
      label: 'Marcas > 60%',
      value: `${above.length} / ${brands.length}`,
      sub: aboveNames || '—',
      accent: 'oklch(0.78 0.16 145)',
      symbol: '●',
    },
    {
      label: 'En zona crítica',
      value: `${critical.length} / ${brands.length}`,
      sub: critNames || '—',
      accent: 'oklch(0.70 0.18 27)',
      symbol: '●',
    },
    {
      label: 'Mejor marca',
      value: best ? `${best.grupoMarca}` : '—',
      sub: best ? `${best.pct.toFixed(1)}%` : '',
      accent: 'oklch(0.78 0.16 70)',
      symbol: '▲',
    },
    {
      label: 'Peor marca',
      value: worst ? `${worst.grupoMarca}` : '—',
      sub: worst ? `${worst.pct.toFixed(1)}%` : '',
      accent: 'oklch(0.70 0.18 27)',
      symbol: '▼',
    },
  ];

  return (
    <div className="mt-[22px] grid grid-cols-2 md:grid-cols-4 gap-3">
      {stats.map(({ label, value, sub, accent, symbol }) => (
        <div
          key={label}
          className="bg-bg-1 border border-line rounded-xl px-[18px] py-4
                     flex items-center justify-between"
        >
          <div>
            <div
              className="font-sans font-semibold uppercase text-ink-2 mb-1"
              style={{ fontSize: 10, letterSpacing: '0.16em' }}
            >
              {label}
            </div>
            <div
              className="font-mono font-bold text-ink-0"
              style={{ fontSize: 20, letterSpacing: '-0.02em' }}
            >
              {value}
            </div>
            {sub && (
              <div className="text-ink-3 mt-0.5" style={{ fontSize: 10 }}>
                {sub}
              </div>
            )}
          </div>
          <div
            className="font-mono opacity-40 text-[26px]"
            style={{ color: accent }}
            aria-hidden="true"
          >
            {symbol}
          </div>
        </div>
      ))}
    </div>
  );
}
