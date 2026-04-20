/**
 * Componente de mapa: react-map-gl + deck.gl ScatterplotLayer.
 * Recibe los datos ya cargados y construye los layers.
 */
import { useMemo, useState, useCallback } from 'react';
import { Map } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { DeckGLOverlay } from '../../utils/DeckGLOverlay';
import { buildClientesLayer, type HoverInfo } from './VentasMapaLayers';
import VentasMapaHoverCard from './VentasMapaHoverCard';
import type { VentasCliente, VentasMetrica } from '../../types/ventas';
import { MAP_INITIAL_VIEW, DARK } from '../../lib/ventas-constants';
import { useVentasHover } from '../../hooks/ventas-mapa/use-ventas-hover';

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY as string | undefined;
const MAP_STYLE = MAPTILER_KEY
  ? `https://api.maptiler.com/maps/streets-dark/style.json?key=${MAPTILER_KEY}`
  : null;

interface VentasMapaProps {
  data: VentasCliente[];
  metrica: VentasMetrica;
  fechaIni: string;
  fechaFin: string;
}

export default function VentasMapa({ data, metrica, fechaIni, fechaFin }: VentasMapaProps) {
  const [hoverInfo, setHoverInfo] = useState<HoverInfo>({ object: null, x: 0, y: 0 });

  const handleHover = useCallback((info: HoverInfo) => {
    setHoverInfo(info);
  }, []);

  const handleClick = useCallback(({ object }: { object: VentasCliente }) => {
    window.open(`/ventas/cliente/${object.id_cliente}`, '_blank');
  }, []);

  const layers = useMemo(
    () =>
      data.length > 0
        ? [buildClientesLayer({ data, metrica, onHover: handleHover, onClick: handleClick })]
        : [],
    [data, metrica, handleHover, handleClick],
  );

  // Hover data query — solo cuando hay un cliente hovereado
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

      {/* Hover card — montado fuera del mapa para evitar overflow:hidden */}
      {hoverInfo.object && (
        <VentasMapaHoverCard
          cliente={hoverInfo.object}
          hoverData={hoverData ?? null}
          x={hoverInfo.x}
          y={hoverInfo.y}
        />
      )}

      {/* Contador de clientes */}
      {data.length > 0 && (
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
    </div>
  );
}
