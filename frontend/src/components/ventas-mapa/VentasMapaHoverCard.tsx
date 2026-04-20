/**
 * Hover card estilo Bloomberg (monospace) para un cliente en el mapa.
 * Se posiciona con coordenadas absolutas de pixel del pickingInfo de deck.gl.
 */
import type { VentasCliente, VentasHoverCliente } from '../../types/ventas';
import { DARK } from '../../lib/ventas-constants';

const LABEL_WIDTH = 14;
const VALUE_WIDTH = 6;

function pad(str: string, len: number): string {
  return str.slice(0, len).padEnd(len);
}

function padLeft(str: string, len: number): string {
  return String(str).padStart(len);
}

const SEPARATOR = '─'.repeat(30);

interface VentasMapaHoverCardProps {
  cliente: VentasCliente;
  hoverData: VentasHoverCliente | null;
  x: number;
  y: number;
}

export default function VentasMapaHoverCard({
  cliente,
  hoverData,
  x,
  y,
}: VentasMapaHoverCardProps) {
  const nombre = cliente.fantasia ?? cliente.razon_social;

  // Offset para no tapar el cursor
  const LEFT_OFFSET = 16;
  const TOP_OFFSET = -20;

  const style: React.CSSProperties = {
    position: 'fixed',
    left: x + LEFT_OFFSET,
    top: y + TOP_OFFSET,
    zIndex: 1000,
    pointerEvents: 'none',
    fontFamily: '"Courier New", Courier, monospace',
    fontSize: '11px',
    lineHeight: '1.6',
    color: '#000',
    backgroundColor: 'rgba(255, 255, 255, 0.96)',
    border: `1px solid ${DARK.border}`,
    borderRadius: '4px',
    padding: '8px 10px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
    whiteSpace: 'pre',
    minWidth: '200px',
    maxWidth: '260px',
  };

  return (
    <div style={style}>
      {/* Título */}
      <div style={{ fontWeight: 'bold', marginBottom: '2px' }}>
        {nombre.toUpperCase().slice(0, 28)}
      </div>
      <div>{SEPARATOR}</div>

      {/* Metadata */}
      {cliente.ruta && (
        <div>{pad('Ruta', 10)}{cliente.ruta.slice(0, 20)}</div>
      )}
      {cliente.preventista && (
        <div>{pad('Prev', 10)}{cliente.preventista.slice(0, 20)}</div>
      )}
      {cliente.sucursal && (
        <div>{pad('Suc', 10)}{cliente.sucursal.slice(0, 20)}</div>
      )}
      {cliente.canal && (
        <div>{pad('Canal', 10)}{cliente.canal.slice(0, 20)}</div>
      )}

      <div>{SEPARATOR}</div>

      {/* Métricas principales */}
      <div>
        <span style={{ fontWeight: 'bold' }}>
          {pad('Bultos', 10)}{padLeft(String(Math.round(cliente.bultos)), VALUE_WIDTH)}
        </span>
        {'  '}
        <span>
          {pad('Docs', 6)}{padLeft(String(cliente.documentos), 4)}
        </span>
      </div>

      {/* Genéricos */}
      {hoverData && hoverData.genericos.length > 0 && (
        <>
          <div>{SEPARATOR}</div>
          {hoverData.genericos.map((g) => (
            <div key={g.generico}>
              <span>{pad(g.generico, LABEL_WIDTH)}</span>
              <span style={{ fontWeight: 'bold' }}>{padLeft(String(Math.round(g.m_act)), VALUE_WIDTH)}</span>
              <span> | </span>
              <span>{padLeft(String(Math.round(g.m_ant)), VALUE_WIDTH)}</span>
            </div>
          ))}
        </>
      )}

      {!hoverData && (
        <>
          <div>{SEPARATOR}</div>
          <div style={{ color: DARK.textMuted, fontSize: '10px' }}>Cargando detalle…</div>
        </>
      )}
    </div>
  );
}
