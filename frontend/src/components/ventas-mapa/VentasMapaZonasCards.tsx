/**
 * Cards de detalle para las zonas visibles.
 * Se muestra debajo del mapa cuando hay más de ZONE_BADGE_THRESHOLD zonas.
 * Cada card tiene: nombre, n_clientes, compradores MAct/MAnt, bultos MAct/MAnt
 * y top genéricos.
 */
import type { VentasZona } from '../../types/ventas';
import { DARK, ZONE_COLORS } from '../../lib/ventas-constants';

interface ZonaCardProps {
  zona: VentasZona;
}

function ZonaCard({ zona }: ZonaCardProps) {
  const [r, g, b] = ZONE_COLORS[zona.color_idx % ZONE_COLORS.length];
  const { metricas } = zona;

  const topGenericos = metricas.por_generico
    .filter((g) => g.m_act > 0 || g.m_ant > 0)
    .slice(0, 4);

  return (
    <div
      style={{
        backgroundColor: DARK.card,
        border: `1px solid ${DARK.border}`,
        borderTop: `3px solid rgb(${r},${g},${b})`,
        borderRadius: '6px',
        padding: '12px',
        minWidth: '200px',
        maxWidth: '260px',
        flex: '1 1 200px',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '8px',
        }}
      >
        <span
          style={{
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            backgroundColor: `rgb(${r},${g},${b})`,
            flexShrink: 0,
          }}
        />
        <span
          style={{
            fontSize: '12px',
            fontWeight: '700',
            color: DARK.text,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
          title={zona.nombre}
        >
          {zona.nombre}
        </span>
      </div>

      {/* Métricas resumen */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '4px',
          marginBottom: '8px',
          fontSize: '11px',
        }}
      >
        <MetricItem label="Clientes" value={zona.n_clientes} />
        <MetricItem label="Compradores" value={metricas.compradores_m_act} prev={metricas.compradores_m_ant} />
        <MetricItem label="Bultos" value={metricas.bultos_m_act} prev={metricas.bultos_m_ant} span />
      </div>

      {/* Genéricos */}
      {topGenericos.length > 0 && (
        <div style={{ borderTop: `1px solid ${DARK.border}`, paddingTop: '6px' }}>
          {topGenericos.map((g) => (
            <div
              key={g.generico}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '10px',
                color: DARK.textSecondary,
                marginBottom: '2px',
              }}
            >
              <span
                style={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  maxWidth: '120px',
                }}
              >
                {g.generico}
              </span>
              <span style={{ flexShrink: 0, color: DARK.text, fontWeight: '600' }}>
                {Math.round(g.m_act).toLocaleString('es-AR')}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MetricItem({
  label,
  value,
  prev,
  span = false,
}: {
  label: string;
  value: number;
  prev?: number;
  span?: boolean;
}) {
  const delta =
    prev !== undefined && prev > 0
      ? ((value - prev) / prev) * 100
      : null;

  return (
    <div
      style={{
        backgroundColor: DARK.surface,
        borderRadius: '4px',
        padding: '4px 6px',
        gridColumn: span ? '1 / -1' : undefined,
      }}
    >
      <div style={{ fontSize: '9px', color: DARK.textMuted, textTransform: 'uppercase' }}>
        {label}
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
        <span style={{ fontSize: '13px', fontWeight: '700', color: DARK.text }}>
          {Math.round(value).toLocaleString('es-AR')}
        </span>
        {delta !== null && (
          <span
            style={{
              fontSize: '9px',
              color: delta >= 0 ? DARK.accentGreen : DARK.accentRed,
            }}
          >
            {delta >= 0 ? '+' : ''}{delta.toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  );
}

interface VentasMapaZonasCardsProps {
  zonas: VentasZona[];
}

export default function VentasMapaZonasCards({ zonas }: VentasMapaZonasCardsProps) {
  return (
    <div
      style={{
        padding: '12px 16px',
        backgroundColor: DARK.bg,
        borderTop: `1px solid ${DARK.border}`,
      }}
    >
      <div
        style={{
          fontSize: '11px',
          fontWeight: '700',
          color: DARK.textSecondary,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginBottom: '10px',
        }}
      >
        Detalle de zonas ({zonas.length})
      </div>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px',
          overflowX: 'auto',
        }}
      >
        {zonas.map((z) => (
          <ZonaCard key={z.nombre} zona={z} />
        ))}
      </div>
    </div>
  );
}
