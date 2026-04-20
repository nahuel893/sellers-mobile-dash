/**
 * Badges overlay para zonas visibles en el mapa.
 *
 * Si ≤ ZONE_BADGE_THRESHOLD zonas: renders pills individuales con nombres.
 * Si > ZONE_BADGE_THRESHOLD zonas: renders UNA pill resumen "N zonas".
 *
 * Se posiciona en absolute sobre el mapa (top, centrado).
 */
import type { VentasZona } from '../../types/ventas';
import { DARK, ZONE_COLORS, ZONE_BADGE_THRESHOLD } from '../../lib/ventas-constants';

interface VentasMapaZonasBadgesProps {
  zonas: VentasZona[];
  agrupacion: 'ruta' | 'preventista';
}

function ZonaPill({ zona }: { zona: VentasZona }) {
  const [r, g, b] = ZONE_COLORS[zona.color_idx % ZONE_COLORS.length];

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: '3px 8px',
        backgroundColor: 'rgba(15,17,23,0.85)',
        border: `1px solid rgba(${r},${g},${b},0.6)`,
        borderRadius: '12px',
        fontSize: '11px',
        color: DARK.text,
        whiteSpace: 'nowrap',
        flexShrink: 0,
      }}
    >
      <span
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: `rgb(${r},${g},${b})`,
          flexShrink: 0,
        }}
      />
      <span>{zona.nombre}</span>
      <span style={{ color: DARK.textMuted, fontSize: '10px' }}>
        {zona.n_clientes}
      </span>
    </div>
  );
}

function CollapsedPill({
  count,
  agrupacion,
}: {
  count: number;
  agrupacion: 'ruta' | 'preventista';
}) {
  const label = agrupacion === 'ruta' ? 'rutas' : 'preventistas';
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: '4px 12px',
        backgroundColor: 'rgba(15,17,23,0.9)',
        border: `1px solid ${DARK.border}`,
        borderRadius: '12px',
        fontSize: '12px',
        color: DARK.text,
      }}
    >
      <span>📍</span>
      <span style={{ fontWeight: '600' }}>{count}</span>
      <span style={{ color: DARK.textSecondary }}>{label} — ver detalle abajo</span>
    </div>
  );
}

export default function VentasMapaZonasBadges({
  zonas,
  agrupacion,
}: VentasMapaZonasBadgesProps) {
  if (zonas.length === 0) return null;

  const isCollapsed = zonas.length > ZONE_BADGE_THRESHOLD;

  return (
    <div
      style={{
        position: 'absolute',
        top: '10px',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 50,
        display: 'flex',
        flexWrap: 'wrap',
        gap: '6px',
        justifyContent: 'center',
        maxWidth: '90%',
        pointerEvents: 'none',
      }}
    >
      {isCollapsed ? (
        <CollapsedPill count={zonas.length} agrupacion={agrupacion} />
      ) : (
        zonas.map((z) => <ZonaPill key={z.nombre} zona={z} />)
      )}
    </div>
  );
}
