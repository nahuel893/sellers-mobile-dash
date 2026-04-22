import { memo } from 'react';
import { BrandSparkline } from './BrandSparkline';
import { BRAND_TO_TOKEN, BRAND_TO_DOT } from '../../lib/brand-colors';
import { fmtNum, fmtPctPp } from '../../lib/format';

export interface BrandCardProps {
  grupoMarca: string;
  pct: number;
  deltaPp: number | null;
  vendido: number;
  cupo: number;
  falta: number;
  ventaDiaRequerida: number;
  rank: number;
  sparklinePoints: number[];
  daysElapsedPct: number;
}

function BrandCardBase({
  grupoMarca,
  pct,
  deltaPp,
  vendido,
  cupo,
  falta,
  ventaDiaRequerida,
  rank,
  sparklinePoints,
  daysElapsedPct,
}: BrandCardProps) {
  const colorToken = BRAND_TO_TOKEN[grupoMarca] ?? 'info';
  const dotClass = BRAND_TO_DOT[grupoMarca] ?? 'bg-info';

  const clampedPct = Math.max(0, Math.min(100, pct));
  const clampedElapsed = Math.max(0, Math.min(100, daysElapsedPct));

  const rankStr = `#${String(rank).padStart(2, '0')}`;
  const deltaStr = fmtPctPp(deltaPp);
  const isDeltaPositive = deltaPp !== null && deltaPp >= 0;

  return (
    <article
      className="bg-bg-1 border border-line rounded-[14px] p-4 md:p-[18px] relative overflow-hidden
                 transition-colors duration-200 hover:border-line-2"
      role="region"
      aria-label={`Marca ${grupoMarca}`}
      style={{
        ['--card-color' as string]: `var(--color-${colorToken}, currentColor)`,
        ['--card-progress' as string]: `${clampedPct}%`,
      }}
    >
      {/* Top progress strip (2px) */}
      <div
        className="absolute top-0 left-0 h-[2px] rounded-br-[2px]"
        style={{
          width: `${clampedPct}%`,
          background: `var(--color-${colorToken})`,
        }}
        aria-hidden="true"
      />

      {/* Card head */}
      <div className="flex items-center justify-between mb-3.5">
        <div className="flex items-center gap-2.5">
          {/* Glowing dot */}
          <span
            className={`rounded-full flex-shrink-0 ${dotClass}`}
            style={{
              width: 8,
              height: 8,
              boxShadow: `0 0 10px var(--color-${colorToken})`,
            }}
            aria-hidden="true"
          />
          <h3
            className="font-sans font-semibold uppercase text-ink-0 m-0 p-0"
            style={{ fontSize: 13, letterSpacing: '0.04em' }}
          >
            {grupoMarca}
          </h3>
        </div>
        <span
          className="font-mono text-ink-3"
          style={{ fontSize: 11, fontWeight: 500 }}
          aria-label={`Ranking ${rankStr}`}
        >
          {rankStr}
        </span>
      </div>

      {/* Percent + delta */}
      <div className="flex items-baseline gap-2.5 mb-1">
        <div
          className="font-mono font-bold text-ink-0 leading-none"
          style={{ fontSize: 38, letterSpacing: '-0.03em' }}
        >
          {Math.floor(clampedPct)}
          <span className="text-ink-2" style={{ fontSize: 22 }}>%</span>
        </div>

        {deltaPp !== null && (
          <span
            className="font-mono font-semibold rounded-[5px] px-[7px] py-[3px]"
            style={{
              fontSize: 12,
              color: isDeltaPositive ? 'oklch(0.78 0.16 145)' : 'oklch(0.70 0.18 27)',
              background: isDeltaPositive
                ? 'color-mix(in oklch, oklch(0.78 0.16 145) 14%, transparent)'
                : 'color-mix(in oklch, oklch(0.70 0.18 27) 14%, transparent)',
            }}
          >
            {deltaStr}
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div
        className="relative bg-bg-3 rounded-[4px] my-3.5"
        style={{ height: 6 }}
      >
        {/* Fill */}
        <div
          className="absolute left-0 top-0 h-full rounded-[4px]"
          style={{
            width: `${clampedPct}%`,
            background: `var(--color-${colorToken})`,
          }}
        />
        {/* HOY tick */}
        <div
          className="absolute top-[-3px] bg-ink-2 rounded-sm"
          style={{
            left: `${clampedElapsed}%`,
            transform: 'translateX(-50%)',
            width: 2,
            height: 12,
          }}
          aria-hidden="true"
        />
      </div>

      {/* KPI grid — 3 columns */}
      <div
        className="grid grid-cols-3 gap-2 pt-3.5"
        style={{ borderTop: '1px solid var(--color-line, #2e2a20)' }}
      >
        <div className="flex flex-col gap-1">
          <span
            className="font-sans font-semibold uppercase text-ink-3"
            style={{ fontSize: 9, letterSpacing: '0.14em' }}
          >
            Vendido
          </span>
          <span
            className="font-mono font-semibold text-ink-1"
            style={{ fontSize: 15, letterSpacing: '-0.01em' }}
          >
            {fmtNum(vendido)}
          </span>
        </div>

        <div className="flex flex-col gap-1">
          <span
            className="font-sans font-semibold uppercase text-ink-3"
            style={{ fontSize: 9, letterSpacing: '0.14em' }}
          >
            Cupo
          </span>
          <span
            className="font-mono font-semibold text-ink-1"
            style={{ fontSize: 15, letterSpacing: '-0.01em' }}
          >
            {fmtNum(cupo)}
          </span>
        </div>

        <div className="flex flex-col gap-1">
          <span
            className="font-sans font-semibold uppercase text-ink-3"
            style={{ fontSize: 9, letterSpacing: '0.14em' }}
          >
            Falta
          </span>
          <span
            className="font-mono font-semibold"
            style={{ fontSize: 15, letterSpacing: '-0.01em', color: 'oklch(0.70 0.18 27)' }}
          >
            {fmtNum(falta)}
          </span>
        </div>
      </div>

      {/* Sparkline */}
      <div className="mt-3">
        <BrandSparkline points={sparklinePoints} colorToken={colorToken} />
      </div>

      {/* Sub-grid: Vta/día req + caption */}
      <div className="grid grid-cols-2 gap-2 mt-2">
        <div className="flex flex-col gap-[3px]">
          <span
            className="font-sans font-semibold uppercase text-ink-3"
            style={{ fontSize: 9, letterSpacing: '0.14em' }}
          >
            Vta/día req.
          </span>
          <span
            className="font-mono font-semibold"
            style={{ fontSize: 14, color: 'oklch(0.86 0.18 115)', letterSpacing: '-0.01em' }}
          >
            {fmtNum(ventaDiaRequerida)}
          </span>
        </div>
        <div className="flex items-end">
          <span
            className="text-ink-3 font-sans"
            style={{ fontSize: 10 }}
          >
            Últimos 18 días — tendencia
          </span>
        </div>
      </div>
    </article>
  );
}

export const BrandCard = memo(BrandCardBase);
