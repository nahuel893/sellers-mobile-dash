import { memo, useMemo } from 'react';

interface BrandSparklineProps {
  /** Daily sales values (last N days) */
  points: number[];
  /** Tailwind semantic color token: 'info'|'ok'|'warn'|'lime'|'violet'|'danger' */
  colorToken: string;
}

/** Builds SVG path strings from a point array within a 100×100 viewBox */
function buildPaths(pts: number[]): { area: string; line: string; lastX: number; lastY: number } {
  if (pts.length === 0) {
    return { area: 'M 0 50 L 100 50', line: 'M 0 50 L 100 50', lastX: 100, lastY: 50 };
  }

  const max = Math.max(...pts);
  const min = Math.min(...pts);
  const range = max - min;

  const normalize = (v: number) => {
    if (range === 0) return 50;
    // flip: high value → small y (top)
    return 90 - ((v - min) / range) * 80;
  };

  const n = pts.length;
  const xStep = n === 1 ? 0 : 100 / (n - 1);

  const coords = pts.map((v, i) => ({
    x: i * xStep,
    y: normalize(v),
  }));

  const lastPt = coords[coords.length - 1];

  // Line path
  const lineParts = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`);
  const linePath = lineParts.join(' ');

  // Area path (close to bottom)
  const firstX = coords[0].x.toFixed(1);
  const lastX = lastPt.x.toFixed(1);
  const areaPath = `${linePath} L ${lastX} 100 L ${firstX} 100 Z`;

  return { area: areaPath, line: linePath, lastX: lastPt.x, lastY: lastPt.y };
}

function BrandSparklineBase({ points, colorToken }: BrandSparklineProps) {
  const pathData = useMemo(() => buildPaths(points), [points.join(',')]);

  return (
    <div
      className={`w-full text-${colorToken}`}
      style={{ height: 28 }}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        width="100%"
        height="100%"
      >
        {/* Area fill */}
        <path
          d={pathData.area}
          fill="currentColor"
          fillOpacity={0.12}
          stroke="none"
        />
        {/* Line */}
        <path
          d={pathData.line}
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          strokeOpacity={0.9}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Last point dot */}
        <circle
          cx={pathData.lastX}
          cy={pathData.lastY}
          r={2}
          fill="currentColor"
        />
      </svg>
    </div>
  );
}

export const BrandSparkline = memo(
  BrandSparklineBase,
  (prev, next) =>
    prev.points.join(',') === next.points.join(',') &&
    prev.colorToken === next.colorToken,
);
