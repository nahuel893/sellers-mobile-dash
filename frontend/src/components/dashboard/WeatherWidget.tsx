import { useWeather } from '../../hooks/use-weather';
import { fmtDateShort } from '../../lib/format';

interface WeatherWidgetProps {
  /** 'desktop' = embedded inside hero; 'mobile' = standalone full-width card */
  variant?: 'desktop' | 'mobile';
  /** City key passed to useWeather (default 'salta') */
  city?: string;
}

function SkeletonWeather() {
  return (
    <div className="animate-pulse space-y-3 p-1">
      <div className="flex justify-between">
        <div className="h-3 bg-white/10 rounded w-24" />
        <div className="h-3 bg-white/10 rounded w-20" />
      </div>
      <div className="flex items-center gap-4">
        <div className="h-16 w-16 bg-white/10 rounded-full flex-shrink-0" />
        <div className="h-12 w-16 bg-white/10 rounded" />
        <div className="space-y-2 flex-1">
          <div className="h-3 bg-white/10 rounded w-28" />
          <div className="h-3 bg-white/10 rounded w-20" />
        </div>
      </div>
      <div className="h-px bg-white/10 mt-3" />
      <div className="grid grid-cols-3 gap-2">
        {[0, 1, 2].map((i) => (
          <div key={i} className="space-y-1">
            <div className="h-2 bg-white/10 rounded w-12" />
            <div className="h-4 bg-white/10 rounded w-10" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function WeatherWidget({ variant = 'desktop', city = 'salta' }: WeatherWidgetProps) {
  const { data, isLoading } = useWeather(city);

  const isMobile = variant === 'mobile';

  const containerClass = isMobile
    ? 'mx-4 my-4 rounded-2xl'
    : 'mt-[18px] rounded-[14px]';

  return (
    <div
      className={`relative overflow-hidden ${containerClass}`}
      style={{
        padding: isMobile ? '18px' : '18px 20px',
        background: 'linear-gradient(135deg, #1a2740 0%, #0f1624 55%, #0a0d14 100%)',
        border: '1px solid #2a3550',
        color: '#e8eaf0',
      }}
    >
      {/* Sun glow decoration */}
      <div
        className="absolute pointer-events-none rounded-full"
        style={{
          top: isMobile ? -40 : -30,
          right: isMobile ? -30 : -30,
          width: isMobile ? 180 : 160,
          height: isMobile ? 180 : 160,
          background: 'radial-gradient(circle, rgba(255, 206, 120, 0.45), transparent 65%)',
        }}
        aria-hidden="true"
      />

      {/* Dot grid accent */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.05) 1px, transparent 1px)',
          backgroundSize: '14px 14px',
        }}
        aria-hidden="true"
      />

      {isLoading ? (
        <SkeletonWeather />
      ) : (
        <div className="relative z-10">
          {/* Header */}
          <div className="flex justify-between items-center mb-3.5">
            {/* Location chip */}
            <div
              className="flex items-center gap-2 font-sans font-semibold uppercase"
              style={{ fontSize: 11, letterSpacing: '0.14em', color: '#c7cfe0' }}
            >
              {/* Glowing dot */}
              <span
                className="flex-shrink-0 rounded-full"
                style={{
                  width: 6,
                  height: 6,
                  background: '#ffcf70',
                  boxShadow: '0 0 8px #ffcf70',
                }}
                aria-hidden="true"
              />
              {data?.city ?? 'Salta Capital'}
            </div>

            {/* Date stamp */}
            <div
              className="font-mono"
              style={{ fontSize: 11, color: '#8892a8', letterSpacing: '0.02em' }}
            >
              {data?.observed_at ? fmtDateShort(data.observed_at) : '—'}
            </div>
          </div>

          {/* Main row */}
          <div className="flex items-center gap-[22px]">
            {/* Sun + cloud illustration */}
            <div
              className="relative flex-shrink-0"
              style={{ width: isMobile ? 64 : 80, height: isMobile ? 64 : 80 }}
              aria-hidden="true"
            >
              {/* Sun disc */}
              <div
                className="absolute rounded-full"
                style={{
                  left: isMobile ? 6 : 8,
                  top: isMobile ? 6 : 8,
                  width: isMobile ? 42 : 52,
                  height: isMobile ? 42 : 52,
                  background: 'radial-gradient(circle at 35% 35%, #fff3cc, #ffce70 55%, #f39c1f)',
                  boxShadow: isMobile
                    ? '0 0 26px rgba(255, 206, 112, 0.55)'
                    : '0 0 32px rgba(255, 206, 112, 0.55), 0 0 64px rgba(255, 206, 112, 0.25)',
                }}
              />
              {/* Cloud */}
              <div
                className="absolute"
                style={{
                  right: 0,
                  bottom: 4,
                  width: isMobile ? 38 : 48,
                  height: isMobile ? 16 : 20,
                  background: '#c7cfe0',
                  borderRadius: isMobile ? '18px 18px 18px 3px' : '20px 20px 20px 4px',
                  boxShadow: isMobile
                    ? '-11px -5px 0 -3px #c7cfe0, 11px 0 0 -3px #b2bbd1'
                    : '-14px -6px 0 -4px #c7cfe0, 14px 0 0 -4px #b2bbd1',
                  opacity: 0.9,
                }}
              />
            </div>

            {/* Temperature */}
            <div
              className="font-mono font-bold"
              style={{
                fontSize: isMobile ? 52 : 64,
                lineHeight: 0.9,
                letterSpacing: '-0.04em',
                color: '#f5f7fb',
              }}
            >
              {data?.temp_c ?? '—'}
              <span style={{ color: '#8892a8', fontWeight: 400, fontSize: isMobile ? 28 : 34 }}>°</span>
            </div>

            {/* Condition */}
            <div className="flex flex-col gap-1 flex-1">
              <div style={{ fontSize: isMobile ? 13 : 14, fontWeight: 600, color: '#e8eaf0' }}>
                {data?.condition ?? 'Desconocido'}
              </div>
              <div
                className="flex gap-2.5 font-mono"
                style={{ fontSize: isMobile ? 10 : 11, color: '#8892a8' }}
              >
                <span style={{ color: '#ffb347' }}>↑ {data?.max_c ?? '—'}°</span>
                <span style={{ color: '#7cc5ff' }}>↓ {data?.min_c ?? '—'}°</span>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div
            className="grid grid-cols-3 mt-4 pt-3.5"
            style={{ borderTop: '1px solid rgba(255,255,255,0.08)' }}
          >
            {[
              { label: 'Sensación', value: data?.feels_like_c, unit: '°' },
              { label: 'Humedad',   value: data?.humidity_pct, unit: '%' },
              { label: 'Viento',    value: data?.wind_kmh,     unit: ' km/h' },
            ].map(({ label, value, unit }, idx) => (
              <div
                key={label}
                className="flex flex-col gap-[3px]"
                style={{
                  paddingRight: idx < 2 ? (isMobile ? 8 : 10) : 0,
                  paddingLeft: idx > 0 ? (isMobile ? 12 : 12) : 0,
                  borderLeft: idx > 0 ? '1px solid rgba(255,255,255,0.08)' : 'none',
                }}
              >
                <span
                  className="font-sans font-semibold uppercase"
                  style={{ fontSize: 9, letterSpacing: '0.16em', color: '#8892a8' }}
                >
                  {label}
                </span>
                <span
                  className="font-mono font-semibold"
                  style={{ fontSize: isMobile ? 13 : 14, color: '#e8eaf0', letterSpacing: '-0.01em' }}
                >
                  {value ?? '—'}
                  <span style={{ color: '#8892a8', fontWeight: 400, fontSize: isMobile ? 10 : 11, marginLeft: 1 }}>
                    {unit}
                  </span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
