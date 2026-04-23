import { memo } from 'react';

export type RadialTone = 'danger-warn' | 'warn-lime' | 'ok-lime';

interface RadialProgressProps {
  /** Percentage value 0-100 */
  pct: number;
  /** SVG size in px (default 180) */
  size?: number;
  /** Stroke width in px (default 14) */
  strokeWidth?: number;
  /** Color tone: controls gradient stops (default: derived from pct) */
  tone?: RadialTone;
}

/** Derives tone from percentage per RF-HERO-06 thresholds */
function toneFromPct(pct: number): RadialTone {
  if (pct < 65) return 'danger-warn';
  if (pct < 76) return 'warn-lime';
  return 'ok-lime';
}

// Use CSS vars from Tailwind-injected custom properties
const STOP_COLORS: Record<RadialTone, [string, string]> = {
  'danger-warn': ['oklch(0.70 0.18 27)', 'oklch(0.78 0.16 70)'],
  'warn-lime':   ['oklch(0.78 0.16 70)',  'oklch(0.86 0.18 115)'],
  'ok-lime':     ['oklch(0.78 0.16 145)', 'oklch(0.86 0.18 115)'],
};

function RadialProgressBase({
  pct,
  size = 180,
  strokeWidth = 14,
  tone,
}: RadialProgressProps) {
  const resolvedTone = tone ?? toneFromPct(pct);
  const [stop1, stop2] = STOP_COLORS[resolvedTone];

  // r = (size - strokeWidth) / 2 - 4  ≈ 72 for default params
  const r = (size - strokeWidth) / 2 - 4;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * r;
  // Visual arc tops out at 100 (can't render >1 full circle). Display number goes up to 999.
  const visualPct = Math.max(0, Math.min(100, pct));
  const displayPct = Math.max(0, Math.min(999, pct));
  const dashOffset = (1 - visualPct / 100) * circumference;

  // Unique gradient id based on tone (safe for multiple instances)
  const gradId = `radial-grad-${resolvedTone}`;

  const bigNum = Math.floor(displayPct);
  const decimal = (displayPct % 1).toFixed(1).slice(1); // ".X"

  return (
    <div
      className="relative flex-shrink-0"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Avance: ${displayPct.toFixed(1)}%`}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ transform: 'rotate(-90deg)' }}
        aria-hidden="true"
      >
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={stop1} />
            <stop offset="100%" stopColor={stop2} />
          </linearGradient>
        </defs>
        {/* Background track */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="var(--color-bg-3, #26221a)"
          strokeWidth={strokeWidth}
        />
        {/* Progress arc */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={`url(#${gradId})`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>

      {/* Center overlay (not rotated) */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div
          className="font-mono leading-none"
          style={{ letterSpacing: '-0.02em' }}
        >
          <span className="text-ink-0" style={{ fontSize: 36, fontWeight: 700 }}>
            {bigNum}{decimal}
          </span>
          <span className="text-ink-2" style={{ fontSize: 20 }}>%</span>
        </div>
        <div
          className="text-ink-2 font-sans font-semibold uppercase mt-2"
          style={{ fontSize: 10, letterSpacing: '0.16em' }}
        >
          Avance
        </div>
      </div>
    </div>
  );
}

export const RadialProgress = memo(RadialProgressBase);
