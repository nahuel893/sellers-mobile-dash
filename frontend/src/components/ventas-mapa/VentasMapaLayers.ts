/**
 * Factory de layers deck.gl para el mapa de ventas.
 */
import { ScatterplotLayer, PolygonLayer } from '@deck.gl/layers';
import type { VentasCliente, VentasZona } from '../../types/ventas';
import type { VentasMetrica } from '../../types/ventas';
import {
  COLOR_SCALE_BURBUJAS,
  COLOR_SIN_VENTAS,
  ZONE_COLORS,
  interpolateColor,
  normalize,
  toRadius,
} from '../../lib/ventas-constants';

export interface HoverInfo {
  object: VentasCliente | null;
  x: number;
  y: number;
}

export interface ZonaHoverInfo {
  object: VentasZona | null;
  x: number;
  y: number;
}

interface BuildLayerOptions {
  data: VentasCliente[];
  metrica: VentasMetrica;
  onHover: (info: HoverInfo) => void;
  onClick: (info: { object: VentasCliente }) => void;
}

/**
 * Calcula el valor de la métrica seleccionada para un cliente.
 */
function getMetricaValue(cliente: VentasCliente, metrica: VentasMetrica): number {
  switch (metrica) {
    case 'bultos':
      return cliente.bultos;
    case 'facturacion':
      return cliente.facturacion;
    case 'documentos':
      return cliente.documentos;
  }
}

/**
 * Construye el ScatterplotLayer para los clientes.
 */
export function buildClientesLayer({
  data,
  metrica,
  onHover,
  onClick,
}: BuildLayerOptions): ScatterplotLayer<VentasCliente> {
  // Pre-calcular min/max de la métrica para normalización
  const values = data.map((c) => getMetricaValue(c, metrica));
  const min = Math.min(...values);
  const max = Math.max(...values);

  return new ScatterplotLayer<VentasCliente>({
    id: 'ventas-clientes-layer',
    data,
    pickable: true,
    opacity: 0.85,
    stroked: true,
    filled: true,
    radiusScale: 1,
    radiusMinPixels: 2,
    radiusMaxPixels: 20,
    lineWidthMinPixels: 0,

    getPosition: (d) => [d.longitud, d.latitud],

    getRadius: (d) => {
      const val = getMetricaValue(d, metrica);
      if (val === 0) return 5; // radio fijo para sin ventas, visible pero pequeño
      return toRadius(normalize(val, min, max));
    },

    getFillColor: (d) => {
      const val = getMetricaValue(d, metrica);
      if (val === 0) {
        return [...COLOR_SIN_VENTAS, 255] as [number, number, number, number];
      }
      const t = normalize(val, min, max);
      const [r, g, b] = interpolateColor(t, COLOR_SCALE_BURBUJAS);
      return [r, g, b, 220];
    },

    getLineColor: (d) => {
      const val = getMetricaValue(d, metrica);
      if (val === 0) {
        // Halo blanco para clientes sin ventas
        return [255, 255, 255, 200];
      }
      return [0, 0, 0, 60];
    },

    getLineWidth: (d) => {
      const val = getMetricaValue(d, metrica);
      return val === 0 ? 2 : 0.5;
    },

    onHover: (info) => {
      onHover({
        object: (info.object as VentasCliente) ?? null,
        x: info.x,
        y: info.y,
      });
    },

    onClick: (info) => {
      if (info.object) {
        onClick({ object: info.object as VentasCliente });
      }
    },

    updateTriggers: {
      getFillColor: [metrica, min, max],
      getRadius: [metrica, min, max],
      getLineColor: [metrica],
      getLineWidth: [metrica],
    },
  });
}

// ---------------------------------------------------------------------------
// Zona layer (PolygonLayer)
// ---------------------------------------------------------------------------

/**
 * Oscurece un color RGB en un 30% para usarlo como color de borde.
 */
function darken(color: [number, number, number]): [number, number, number] {
  return [
    Math.round(color[0] * 0.7),
    Math.round(color[1] * 0.7),
    Math.round(color[2] * 0.7),
  ];
}

interface BuildZonasLayerOptions {
  data: VentasZona[];
  onHover: (info: ZonaHoverInfo) => void;
}

/**
 * Construye el PolygonLayer para las zonas convex hull.
 *
 * Alpha 0.3 (76/255) para permitir superposición semitransparente.
 * El borde es el mismo color pero más saturado (sin alpha).
 */
export function buildZonasLayer({
  data,
  onHover,
}: BuildZonasLayerOptions): PolygonLayer<VentasZona> {
  return new PolygonLayer<VentasZona>({
    id: 'ventas-zonas-layer',
    data,
    pickable: true,
    stroked: true,
    filled: true,
    wireframe: false,
    lineWidthMinPixels: 1,
    getLineWidth: 2,

    getPolygon: (z) => z.coords,

    getFillColor: (z) => {
      const [r, g, b] = ZONE_COLORS[z.color_idx % ZONE_COLORS.length];
      return [r, g, b, 76]; // alpha ~0.3
    },

    getLineColor: (z) => {
      const base = ZONE_COLORS[z.color_idx % ZONE_COLORS.length];
      return [...darken(base), 200];
    },

    onHover: (info) => {
      onHover({
        object: (info.object as VentasZona) ?? null,
        x: info.x,
        y: info.y,
      });
    },

    updateTriggers: {
      getFillColor: [data.length],
      getLineColor: [data.length],
    },
  });
}
