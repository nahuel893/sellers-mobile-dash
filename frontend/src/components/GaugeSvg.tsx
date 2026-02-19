interface GaugeSvgProps {
  /** Porcentaje a mostrar (0-150+) */
  value: number;
  /** Máximo del gauge (default 150) */
  max?: number;
  /** Color del arco de valor */
  color: string;
  /** Ancho del trazo (default 20) */
  strokeWidth?: number;
  /** Tamaño de fuente central (default 36) */
  fontSize?: number;
  /** Mostrar tick en 100% (default true) */
  showThreshold?: boolean;
  /** Clase CSS adicional */
  className?: string;
}

export default function GaugeSvg({
  value,
  max = 150,
  color,
  strokeWidth = 20,
  fontSize = 36,
  showThreshold = true,
  className = '',
}: GaugeSvgProps) {
  const cx = 100;
  const cy = 100;
  const r = 80;
  const clampedValue = Math.min(Math.max(value, 0), max);
  const ratio = clampedValue / max;

  // Arco de fondo: 180° (izquierda) a 0° (derecha)
  const bgStartX = cx - r;
  const bgEndX = cx + r;
  const bgPath = `M ${bgStartX},${cy} A ${r},${r} 0 0,1 ${bgEndX},${cy}`;

  // Arco de valor
  const valueAngle = Math.PI - ratio * Math.PI;
  const valueEndX = cx + r * Math.cos(valueAngle);
  const valueEndY = cy - r * Math.sin(valueAngle);
  const largeArc = ratio > 0.5 ? 1 : 0;
  const valuePath =
    ratio > 0
      ? `M ${bgStartX},${cy} A ${r},${r} 0 ${largeArc},1 ${valueEndX.toFixed(2)},${valueEndY.toFixed(2)}`
      : '';

  // Tick de threshold en 100%
  const thresholdRatio = Math.min(100 / max, 1);
  const thresholdAngle = Math.PI - thresholdRatio * Math.PI;
  const tickInner = r - strokeWidth / 2 - 4;
  const tickOuter = r + strokeWidth / 2 + 4;
  const tickX1 = cx + tickInner * Math.cos(thresholdAngle);
  const tickY1 = cy - tickInner * Math.sin(thresholdAngle);
  const tickX2 = cx + tickOuter * Math.cos(thresholdAngle);
  const tickY2 = cy - tickOuter * Math.sin(thresholdAngle);

  return (
    <svg viewBox="0 0 200 120" className={className}>
      {/* Arco de fondo */}
      <path
        d={bgPath}
        fill="none"
        stroke="#e9ecef"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
      />
      {/* Arco de valor */}
      {valuePath && (
        <path
          d={valuePath}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
      )}
      {/* Tick en 100% */}
      {showThreshold && (
        <line
          x1={tickX1.toFixed(2)}
          y1={tickY1.toFixed(2)}
          x2={tickX2.toFixed(2)}
          y2={tickY2.toFixed(2)}
          stroke="#6c757d"
          strokeWidth={2}
          strokeLinecap="round"
        />
      )}
      {/* Texto central */}
      <text
        x={cx}
        y={cy - 5}
        textAnchor="middle"
        dominantBaseline="auto"
        fontSize={fontSize}
        fontWeight={700}
        fontFamily="Inter, sans-serif"
        fill="#1a1a2e"
      >
        {value.toFixed(1)}%
      </text>
    </svg>
  );
}
