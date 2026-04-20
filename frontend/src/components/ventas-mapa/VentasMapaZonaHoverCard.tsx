/**
 * Hover card para una zona convex hull en el mapa.
 * Muestra nombre de ruta/preventista, bultos MAct/MAnt por genérico,
 * compradores y total de clientes.
 *
 * React component (NO deck.gl tooltip) — posicionado con coords absolutas.
 */
import type { VentasZona } from '../../types/ventas';
import { DARK, ZONE_COLORS } from '../../lib/ventas-constants';

const LABEL_WIDTH = 16;
const VALUE_WIDTH = 7;
const SEPARATOR = '─'.repeat(32);

function pad(str: string, len: number): string {
  return str.slice(0, len).padEnd(len);
}

function padLeft(val: number, len: number): string {
  return Math.round(val).toString().padStart(len);
}

interface VentasMapaZonaHoverCardProps {
  zona: VentasZona;
  x: number;
  y: number;
}

export default function VentasMapaZonaHoverCard({
  zona,
  x,
  y,
}: VentasMapaZonaHoverCardProps) {
  const [r, g, b] = ZONE_COLORS[zona.color_idx % ZONE_COLORS.length];
  const colorDot = `rgb(${r},${g},${b})`;

  const style: React.CSSProperties = {
    position: 'fixed',
    left: x + 16,
    top: y - 20,
    zIndex: 1001,
    pointerEvents: 'none',
    fontFamily: '"Courier New", Courier, monospace',
    fontSize: '11px',
    lineHeight: '1.6',
    color: '#000',
    backgroundColor: 'rgba(255, 255, 255, 0.97)',
    border: `1px solid ${DARK.border}`,
    borderLeft: `3px solid ${colorDot}`,
    borderRadius: '4px',
    padding: '8px 10px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
    whiteSpace: 'pre',
    minWidth: '220px',
    maxWidth: '280px',
  };

  const { metricas } = zona;

  return (
    <div style={style}>
      {/* Título */}
      <div style={{ fontWeight: 'bold', marginBottom: '2px' }}>
        {zona.nombre.toUpperCase().slice(0, 30)}
      </div>
      <div>{SEPARATOR}</div>

      {/* Resumen */}
      <div>
        {pad('Clientes', LABEL_WIDTH)}{padLeft(zona.n_clientes, VALUE_WIDTH)}
      </div>
      <div>
        {pad('Compradores', LABEL_WIDTH)}
        <span style={{ fontWeight: 'bold' }}>{padLeft(metricas.compradores_m_act, VALUE_WIDTH)}</span>
        {' | '}
        {padLeft(metricas.compradores_m_ant, VALUE_WIDTH - 1)}
      </div>
      <div>
        {pad('Bultos total', LABEL_WIDTH)}
        <span style={{ fontWeight: 'bold' }}>{padLeft(metricas.bultos_m_act, VALUE_WIDTH)}</span>
        {' | '}
        {padLeft(metricas.bultos_m_ant, VALUE_WIDTH - 1)}
      </div>

      {/* Por genérico */}
      {metricas.por_generico.length > 0 && (
        <>
          <div>{SEPARATOR}</div>
          <div style={{ color: DARK.textMuted, fontSize: '10px', marginBottom: '2px' }}>
            {'GENÉRICO         MAct   MAnt'}
          </div>
          {metricas.por_generico
            .filter((g) => g.m_act > 0 || g.m_ant > 0)
            .slice(0, 6)
            .map((g) => (
              <div key={g.generico}>
                {pad(g.generico, LABEL_WIDTH)}
                <span style={{ fontWeight: 'bold' }}>{padLeft(g.m_act, VALUE_WIDTH)}</span>
                {' | '}
                {padLeft(g.m_ant, VALUE_WIDTH - 1)}
              </div>
            ))}
        </>
      )}
    </div>
  );
}
