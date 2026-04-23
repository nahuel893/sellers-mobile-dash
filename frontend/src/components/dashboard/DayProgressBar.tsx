
interface DayProgressBarProps {
  /** Sales % (0-100) — width of the filled gradient bar */
  pct: number;
  /** Days elapsed as % of the month (0-100) — position of HOY tick */
  daysElapsedPct: number;
  /** Number of days remaining in the month */
  daysRemaining: number;
}

export function DayProgressBar({ pct, daysElapsedPct, daysRemaining }: DayProgressBarProps) {
  // Visual fill tops out at 100 (bar width). aria-label reports the real value up to 999.
  const visualPct = Math.max(0, Math.min(100, pct));
  const displayPct = Math.max(0, Math.min(999, pct));
  const clampedElapsed = Math.max(0, Math.min(100, daysElapsedPct));

  return (
    <div
      className="mt-[22px] pt-[22px] border-t border-line"
      aria-label={`Progreso del mes: ${displayPct.toFixed(1)}%`}
    >
      {/* Header row */}
      <div
        className="flex justify-between items-center mb-3 font-sans font-semibold uppercase text-ink-2"
        style={{ fontSize: 11, letterSpacing: '0.14em' }}
      >
        <span>Progreso del mes</span>
        <span
          className="text-warn font-mono normal-case"
          style={{ fontSize: 12, letterSpacing: 0 }}
        >
          {daysRemaining} días restantes
        </span>
      </div>

      {/* Bar container */}
      <div
        className="relative bg-bg-3 rounded-md overflow-visible"
        style={{ height: 10 }}
      >
        {/* Filled gradient */}
        <div
          className="absolute left-0 top-0 h-full rounded-md"
          style={{
            width: `${visualPct}%`,
            background: 'linear-gradient(90deg, oklch(0.70 0.18 27), oklch(0.78 0.16 70))',
          }}
        />

        {/* HOY tick */}
        <div
          className="absolute top-0"
          style={{
            left: `${clampedElapsed}%`,
            transform: 'translateX(-50%)',
          }}
          aria-hidden="true"
        >
          {/* Label above tick */}
          <div
            className="absolute font-mono font-semibold text-ink-0 whitespace-nowrap"
            style={{
              top: -18,
              left: '50%',
              transform: 'translateX(-50%)',
              fontSize: 9,
              letterSpacing: '0.08em',
            }}
          >
            HOY {Math.round(clampedElapsed)}%
          </div>
          {/* Tick line */}
          <div
            className="bg-ink-0 rounded-sm"
            style={{ width: 2, height: 18, marginTop: -4 }}
          />
        </div>
      </div>

      {/* Caption */}
      <div
        className="text-ink-2 font-sans mt-2"
        style={{ fontSize: 10 }}
      >
        Restan {daysRemaining} días
      </div>
    </div>
  );
}
