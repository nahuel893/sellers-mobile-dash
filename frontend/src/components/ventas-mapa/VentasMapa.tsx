/**
 * Componente de mapa: react-map-gl + deck.gl layers.
 * Soporta tres modos:
 *   - burbujas: ScatterplotLayer (existente)
 *   - calor: HeatmapLayer (difuso) o HexagonLayer (grilla)
 *   - compro: ScatterplotLayer verde/rojo
 */
import { useMemo, useState, useCallback } from 'react';
import { Map } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { DeckGLOverlay } from '../../utils/DeckGLOverlay';
import {
  buildClientesLayer,
  buildZonasLayer,
  buildCalorLayer,
  buildCalorGrillaLayer,
  buildComproLayer,
  type HoverInfo,
  type ZonaHoverInfo,
  type ComproHoverInfo,
} from './VentasMapaLayers';
import VentasMapaHoverCard from './VentasMapaHoverCard';
import VentasMapaZonaHoverCard from './VentasMapaZonaHoverCard';
import VentasMapaZonasBadges from './VentasMapaZonasBadges';
import type { VentasCliente, VentasMetrica, VentasZona, VentasCompro, CalorSubmodo } from '../../types/ventas';
import { MAP_INITIAL_VIEW, DARK } from '../../lib/ventas-constants';
import { useVentasHover } from '../../hooks/ventas-mapa/use-ventas-hover';

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY as string | undefined;
const MAP_STYLE = MAPTILER_KEY
  ? `https://api.maptiler.com/maps/streets-dark/style.json?key=${MAPTILER_KEY}`
  : null;

interface VentasMapaProps {
  /** Clientes para modo burbujas y calor (mismo endpoint /clientes) */
  data: VentasCliente[];
  metrica: VentasMetrica;
  fechaIni: string;
  fechaFin: string;
  zonas?: VentasZona[];
  zonasAgrupacion?: 'ruta' | 'preventista';
  /** Modo de visualización activo */
  modo?: 'burbujas' | 'calor' | 'compro';
  /** Sub-modo dentro de calor */
  calorSubmodo?: CalorSubmodo;
  /** Datos para modo compro (endpoint /compro) */
  dataCompro?: VentasCompro[];
}

export default function VentasMapa({
  data,
  metrica,
  fechaIni,
  fechaFin,
  zonas,
  zonasAgrupacion = 'ruta',
  modo = 'burbujas',
  calorSubmodo = 'difuso',
  dataCompro = [],
}: VentasMapaProps) {
  const [hoverInfo, setHoverInfo] = useState<HoverInfo>({ object: null, x: 0, y: 0 });
  const [zonaHoverInfo, setZonaHoverInfo] = useState<ZonaHoverInfo>({ object: null, x: 0, y: 0 });
  const [comproHoverInfo, setComproHoverInfo] = useState<ComproHoverInfo>({ object: null, x: 0, y: 0 });

  const handleHover = useCallback((info: HoverInfo) => {
    setHoverInfo(info);
    if (info.object) {
      setZonaHoverInfo({ object: null, x: 0, y: 0 });
      setComproHoverInfo({ object: null, x: 0, y: 0 });
    }
  }, []);

  const handleZonaHover = useCallback((info: ZonaHoverInfo) => {
    setZonaHoverInfo(info);
    if (info.object) {
      setHoverInfo({ object: null, x: 0, y: 0 });
      setComproHoverInfo({ object: null, x: 0, y: 0 });
    }
  }, []);

  const handleComproHover = useCallback((info: ComproHoverInfo) => {
    setComproHoverInfo(info);
    if (info.object) {
      setHoverInfo({ object: null, x: 0, y: 0 });
      setZonaHoverInfo({ object: null, x: 0, y: 0 });
    }
  }, []);

  const handleClick = useCallback(({ object }: { object: VentasCliente }) => {
    window.open(`/ventas/cliente/${object.id_cliente}`, '_blank');
  }, []);

  const layers = useMemo(() => {
    const result = [];

    // Zonas siempre van debajo (independiente del modo)
    if (zonas && zonas.length > 0) {
      result.push(buildZonasLayer({ data: zonas, onHover: handleZonaHover }));
    }

    if (modo === 'burbujas' && data.length > 0) {
      result.push(buildClientesLayer({ data, metrica, onHover: handleHover, onClick: handleClick }));
    } else if (modo === 'calor' && data.length > 0) {
      if (calorSubmodo === 'grilla') {
        result.push(buildCalorGrillaLayer(data));
      } else {
        result.push(buildCalorLayer(data));
      }
    } else if (modo === 'compro' && dataCompro.length > 0) {
      result.push(buildComproLayer({ data: dataCompro, onHover: handleComproHover }));
    }

    return result;
  }, [data, metrica, zonas, modo, calorSubmodo, dataCompro, handleHover, handleZonaHover, handleComproHover, handleClick]);

  // Hover data query — solo cuando hay un cliente burbujas hovereado
  const { data: hoverData } = useVentasHover({
    id_cliente: hoverInfo.object?.id_cliente ?? null,
    fecha_ini: fechaIni,
    fecha_fin: fechaFin,
  });

  if (!MAP_STYLE) {
    return (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: DARK.bg,
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <div style={{ fontSize: '32px' }}>🗺️</div>
        <div
          style={{
            backgroundColor: '#fef3cd',
            border: '1px solid #ffc107',
            borderRadius: '6px',
            padding: '16px 24px',
            maxWidth: '420px',
            textAlign: 'center',
            color: '#333',
          }}
        >
          <strong>VITE_MAPTILER_KEY no está configurada.</strong>
          <br />
          <span style={{ fontSize: '13px' }}>
            Configurar la variable de entorno para ver el mapa. Ver{' '}
            <code>docs/env-example.md</code>.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Map
        mapStyle={MAP_STYLE}
        initialViewState={MAP_INITIAL_VIEW}
        style={{ width: '100%', height: '100%' }}
      >
        <DeckGLOverlay layers={layers} />
      </Map>

      {/* Badges de zonas — superpuesto en la parte superior del mapa */}
      {zonas && zonas.length > 0 && (
        <VentasMapaZonasBadges zonas={zonas} agrupacion={zonasAgrupacion} />
      )}

      {/* Hover card de cliente (modo burbujas) */}
      {hoverInfo.object && (
        <VentasMapaHoverCard
          cliente={hoverInfo.object}
          hoverData={hoverData ?? null}
          x={hoverInfo.x}
          y={hoverInfo.y}
        />
      )}

      {/* Hover card de zona */}
      {zonaHoverInfo.object && (
        <VentasMapaZonaHoverCard
          zona={zonaHoverInfo.object}
          x={zonaHoverInfo.x}
          y={zonaHoverInfo.y}
        />
      )}

      {/* Tooltip compro — solo en modo compro */}
      {modo === 'compro' && comproHoverInfo.object && (
        <ComproTooltip info={comproHoverInfo} />
      )}

      {/* Leyenda modo compro */}
      {modo === 'compro' && (
        <ComproLeyenda />
      )}

      {/* Contador de clientes */}
      {modo !== 'compro' && data.length > 0 && (
        <div
          style={{
            position: 'absolute',
            bottom: '32px',
            left: '12px',
            backgroundColor: 'rgba(15,17,23,0.85)',
            border: `1px solid ${DARK.border}`,
            borderRadius: '4px',
            padding: '4px 10px',
            color: DARK.textSecondary,
            fontSize: '11px',
          }}
        >
          {data.length.toLocaleString('es-AR')} clientes
        </div>
      )}

      {modo === 'compro' && dataCompro.length > 0 && (
        <div
          style={{
            position: 'absolute',
            bottom: '32px',
            left: '12px',
            backgroundColor: 'rgba(15,17,23,0.85)',
            border: `1px solid ${DARK.border}`,
            borderRadius: '4px',
            padding: '4px 10px',
            color: DARK.textSecondary,
            fontSize: '11px',
          }}
        >
          {dataCompro.filter((c) => c.compro).length.toLocaleString('es-AR')} compraron ·{' '}
          {dataCompro.filter((c) => !c.compro).length.toLocaleString('es-AR')} no compraron
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-componentes internos
// ---------------------------------------------------------------------------

function ComproTooltip({ info }: { info: ComproHoverInfo }) {
  const { object: c, x, y } = info;
  if (!c) return null;

  const ultimaCompra = c.ultima_compra
    ? new Date(c.ultima_compra + 'T00:00:00').toLocaleDateString('es-AR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      })
    : 'Sin compras';

  return (
    <div
      style={{
        position: 'absolute',
        left: x + 12,
        top: y - 8,
        backgroundColor: 'rgba(15,17,23,0.95)',
        border: `1px solid ${DARK.border}`,
        borderRadius: '6px',
        padding: '8px 12px',
        pointerEvents: 'none',
        zIndex: 10,
        minWidth: '160px',
      }}
    >
      <div style={{ fontSize: '12px', fontWeight: '700', color: DARK.text, marginBottom: '4px' }}>
        Cliente #{c.id_cliente}
      </div>
      <div
        style={{
          fontSize: '11px',
          color: c.compro ? DARK.accentGreen : DARK.accentRed,
          fontWeight: '600',
          marginBottom: '4px',
        }}
      >
        {c.compro ? '● Compró en el período' : '● No compró en el período'}
      </div>
      <div style={{ fontSize: '11px', color: DARK.textSecondary }}>
        Última compra: {ultimaCompra}
      </div>
    </div>
  );
}

function ComproLeyenda() {
  return (
    <div
      style={{
        position: 'absolute',
        top: '12px',
        left: '12px',
        backgroundColor: 'rgba(15,17,23,0.9)',
        border: `1px solid ${DARK.border}`,
        borderRadius: '6px',
        padding: '8px 12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        zIndex: 5,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#27ae60', display: 'inline-block' }} />
        <span style={{ fontSize: '11px', color: DARK.text }}>Compró en el período</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#e74c3c', display: 'inline-block' }} />
        <span style={{ fontSize: '11px', color: DARK.text }}>No compró en el período</span>
      </div>
    </div>
  );
}
