import { RadialProgress } from './RadialProgress';
import { DayProgressBar } from './DayProgressBar';
import { TrendRow } from './TrendRow';
import { fmtNum } from '../../lib/format';

type StatusTone = 'danger' | 'warn' | 'ok';

function statusFromPct(pct: number): { tone: StatusTone; label: string } {
  if (pct < 65) return { tone: 'danger', label: 'BAJO OBJETIVO' };
  if (pct < 76) return { tone: 'warn',   label: 'CERCA' };
  return                { tone: 'ok',     label: 'EN OBJETIVO' };
}

const TONE_COLORS: Record<StatusTone, string> = {
  danger: 'oklch(0.70 0.18 27)',
  warn:   'oklch(0.78 0.16 70)',
  ok:     'oklch(0.78 0.16 145)',
};

export interface GenericBlockProps {
  /** Short eyebrow (e.g. "GENÉRICO" or "GRUPO DE GENÉRICOS") */
  eyebrow: string;
  /** Display name: "Aguas Danone" | "MultiCCU" */
  title: string;
  /** Optional descriptor shown below name (e.g. "Vinos CCU · Sidras · Licores") */
  caption?: string;
  /** Overall % tendencia */
  pct: number;
  /** Vendido (bultos) */
  vendido: number;
  /** Cupo total (bultos) */
  cupo: number;
  /** Falta (bultos) */
  falta: number;
  /** Required daily sales (bultos/day) */
  ventaDiaRequerida: number;
  /** Days elapsed as % of month */
  daysElapsedPct: number;
  /** Days remaining in month */
  daysRemaining: number;
  /** Projected end-of-month (bultos) */
  tendencia: number;
  /** Gap: tendencia - cupo */
  gap: number;
  /** Required daily rhythm to close gap */
  ritmoRequerido: number;
}

/**
 * Large block for generic categories (AGUAS_DANONE, MULTICCU) that do NOT
 * expand into brand cards. Same visual language as HeroCard but compact:
 * - Radial 160px (vs 180 in Hero)
 * - No iniciales / no ruta / no weather
 * - Intended to render side-by-side with another GenericBlock
 */
export function GenericBlock({
  eyebrow,
  title,
  caption,
  pct,
  vendido,
  cupo,
  falta,
  ventaDiaRequerida,
  daysElapsedPct,
  daysRemaining,
  tendencia,
  gap,
  ritmoRequerido,
}: GenericBlockProps) {
  const { tone, label: badgeLabel } = statusFromPct(pct);
  const toneColor = TONE_COLORS[tone];

  return (
    <section
      className="border border-line rounded-[18px] p-7 relative overflow-hidden"
      aria-label={`${title} — avance del mes`}
      style={{
        background: 'linear-gradient(180deg, var(--color-bg-1, #17150f), var(--color-bg-0, #0e0d0b))',
      }}
    >
      {/* Decorative radial glow (top-right) */}
      <div
        className="absolute pointer-events-none rounded-full"
        style={{
          top: -80,
          right: -80,
          width: 280,
          height: 280,
          background: `radial-gradient(circle, color-mix(in oklch, ${toneColor} 18%, transparent), transparent 70%)`,
        }}
        aria-hidden="true"
      />

      {/* ── Head ── */}
      <div className="flex items-start justify-between mb-[18px]">
        <div>
          <div
            className="text-ink-2 font-sans font-semibold uppercase mb-1.5"
            style={{ fontSize: 10, letterSpacing: '0.2em' }}
          >
            {eyebrow}
          </div>
          <h2
            className="text-ink-0 font-sans font-semibold m-0"
            style={{ fontSize: 20, letterSpacing: '-0.01em' }}
          >
            {title}
          </h2>
          {caption && (
            <div
              className="text-ink-3 font-sans mt-1"
              style={{ fontSize: 12, letterSpacing: '0.01em' }}
            >
              {caption}
            </div>
          )}
        </div>

        <div
          className="font-sans font-semibold rounded-[6px] px-2.5 py-[5px] flex-shrink-0"
          style={{
            fontSize: 11,
            letterSpacing: '0.02em',
            color: toneColor,
            background: `color-mix(in oklch, ${toneColor} 14%, transparent)`,
            border: `1px solid color-mix(in oklch, ${toneColor} 30%, transparent)`,
          }}
          role="status"
          aria-label={`Estado: ${badgeLabel}`}
        >
          {badgeLabel}
        </div>
      </div>

      {/* ── Radial row ── */}
      <div className="flex items-center gap-6 py-2 pb-5">
        <div className="flex flex-col items-center gap-2 flex-shrink-0">
          <span
            className="text-ink-2 font-sans font-semibold uppercase"
            style={{ fontSize: 10, letterSpacing: '0.2em' }}
          >
            Tendencia
          </span>
          <RadialProgress pct={pct} size={160} strokeWidth={14} />
        </div>

        <div className="flex flex-col gap-3.5 flex-1">
          {[
            { label: 'Cupo',    value: fmtNum(cupo),             className: 'text-ink-0' },
            { label: 'Venta',   value: fmtNum(vendido),          className: 'text-ink-0' },
            { label: 'Falta',   value: fmtNum(falta),            className: '', style: { color: 'oklch(0.70 0.18 27)' } },
            { label: 'Vta/día', value: fmtNum(ventaDiaRequerida), className: '', style: { color: 'oklch(0.86 0.18 115)' } },
          ].map(({ label, value, className, style }, idx, arr) => (
            <div
              key={label}
              className={`flex justify-between items-baseline pb-3 ${idx < arr.length - 1 ? 'border-b border-dashed border-line' : ''}`}
            >
              <span
                className="text-ink-2 font-sans font-semibold uppercase"
                style={{ fontSize: 11, letterSpacing: '0.14em' }}
              >
                {label}
              </span>
              <span
                className={`font-mono font-semibold ${className}`}
                style={{ fontSize: 19, letterSpacing: '-0.01em', ...style }}
              >
                {value}
              </span>
            </div>
          ))}
        </div>
      </div>

      <DayProgressBar pct={pct} daysElapsedPct={daysElapsedPct} daysRemaining={daysRemaining} />

      <TrendRow
        tendencia={tendencia}
        cupoTotal={cupo}
        gap={gap}
        ritmoRequerido={ritmoRequerido}
      />
    </section>
  );
}
