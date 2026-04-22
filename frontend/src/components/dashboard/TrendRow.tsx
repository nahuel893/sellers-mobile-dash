import { fmtNum } from '../../lib/format';

interface TrendRowProps {
  /** Projected end-of-month volume (hl) */
  tendencia: number;
  /** Total quota (hl) */
  cupoTotal: number;
  /** Gap = tendencia - cupoTotal (positive = surplus, negative = deficit) */
  gap: number;
  /** Required daily rhythm to close the gap (hl/day) */
  ritmoRequerido: number;
}

export function TrendRow({ tendencia, cupoTotal, gap, ritmoRequerido }: TrendRowProps) {
  const pctCierre = cupoTotal > 0 ? (tendencia / cupoTotal) * 100 : 0;
  const isPositiveGap = gap >= 0;

  return (
    <div className="grid grid-cols-2 gap-3 mt-5">
      {/* Tendencia card */}
      <div className="bg-bg-2 border border-line rounded-xl p-[14px]">
        <div
          className="text-ink-2 font-sans font-semibold uppercase mb-1.5"
          style={{ fontSize: 10, letterSpacing: '0.14em' }}
        >
          Tendencia
        </div>
        <div
          className="text-ink-0 font-mono font-semibold"
          style={{ fontSize: 17 }}
        >
          {fmtNum(tendencia)}
        </div>
        <div
          className="font-mono mt-0.5"
          style={{ fontSize: 11, color: isPositiveGap ? 'oklch(0.78 0.16 145)' : 'oklch(0.78 0.16 70)' }}
        >
          proyecta {pctCierre.toFixed(1)}% cierre
        </div>
      </div>

      {/* Gap card */}
      <div className="bg-bg-2 border border-line rounded-xl p-[14px]">
        <div
          className="text-ink-2 font-sans font-semibold uppercase mb-1.5"
          style={{ fontSize: 10, letterSpacing: '0.14em' }}
        >
          Gap vs. objetivo
        </div>
        <div
          className="font-mono font-semibold"
          style={{
            fontSize: 17,
            color: isPositiveGap ? 'oklch(0.78 0.16 145)' : 'oklch(0.70 0.18 27)',
          }}
        >
          {isPositiveGap ? '+' : ''}{fmtNum(gap)}
        </div>
        <div
          className="font-mono mt-0.5"
          style={{
            fontSize: 11,
            color: isPositiveGap ? 'oklch(0.78 0.16 145)' : 'oklch(0.70 0.18 27)',
          }}
        >
          necesita {fmtNum(ritmoRequerido)} hl/día
        </div>
      </div>
    </div>
  );
}
