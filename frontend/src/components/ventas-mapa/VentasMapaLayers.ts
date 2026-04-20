/**
 * Factory de layers deck.gl para el mapa de ventas.
 */
import { ScatterplotLayer, PolygonLayer } from '@deck.gl/layers';
import { HeatmapLayer, HexagonLayer } from '@deck.gl/aggregation-layers';
import type { VentasCliente, VentasZona, VentasCompro } from '../../types/ventas';
import type { VentasMetrica } from '../../types/ventas';
import {
  COLOR_SCALE_BURBUJAS,
  COLOR_SIN_VENTAS,
  ZONE_COLORS,
  CALOR_COLOR_RANGE,
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

// ---------------------------------------------------------------------------
// Calor — HeatmapLayer (modo difuso)
// ---------------------------------------------------------------------------

/**
 * Construye el HeatmapLayer (difuso) a partir de los clientes del mapa.
 * Usa los mismos datos que buildClientesLayer — aggregation client-side.
 */
export function buildCalorLayer(
  data: VentasCliente[],
): HeatmapLayer<VentasCliente> {
  return new HeatmapLayer<VentasCliente>({
    id: 'ventas-calor-layer',
    data,
    pickable: false,
    getPosition: (d) => [d.longitud, d.latitud],
    getWeight: (d) => (d.bultos > 0 ? d.bultos : 1),
    radiusPixels: 30,
    intensity: 1,
    threshold: 0.05,
    colorRange: CALOR_COLOR_RANGE as [number, number, number][],
  });
}

// ---------------------------------------------------------------------------
// Calor — HexagonLayer (modo grilla)
// ---------------------------------------------------------------------------

/**
 * Construye el HexagonLayer (grilla hexagonal) a partir de los clientes del mapa.
 * Aggregation client-side, color por densidad de clientes.
 */
export function buildCalorGrillaLayer(
  data: VentasCliente[],
): HexagonLayer<VentasCliente> {
  return new HexagonLayer<VentasCliente>({
    id: 'ventas-calor-grilla-layer',
    data,
    pickable: false,
    extruded: false,
    radius: 200,
    elevationScale: 4,
    getPosition: (d) => [d.longitud, d.latitud],
    colorRange: CALOR_COLOR_RANGE as [number, number, number][],
  });
}

// ---------------------------------------------------------------------------
// Compro / No-compro — ScatterplotLayer con verde/rojo
// ---------------------------------------------------------------------------

/** Color verde para clientes que compraron en el período (#27ae60) */
const COLOR_COMPRO: [number, number, number, number] = [39, 174, 96, 220];
/** Color rojo para clientes que NO compraron en el período (#e74c3c) */
const COLOR_NO_COMPRO: [number, number, number, number] = [231, 76, 60, 180];

export interface ComproHoverInfo {
  object: VentasCompro | null;
  x: number;
  y: number;
}

interface BuildComproLayerOptions {
  data: VentasCompro[];
  onHover: (info: ComproHoverInfo) => void;
}

/**
 * Construye el ScatterplotLayer para el modo compro/no-compro.
 * Verde = compró en el período, Rojo = no compró.
 * Radio fijo para que la lectura sea categórica, no cuantitativa.
 */
export function buildComproLayer({
  data,
  onHover,
}: BuildComproLayerOptions): ScatterplotLayer<VentasCompro> {
  return new ScatterplotLayer<VentasCompro>({
    id: 'ventas-compro-layer',
    data,
    pickable: true,
    opacity: 0.9,
    stroked: true,
    filled: true,
    radiusMinPixels: 6,
    radiusMaxPixels: 8,
    lineWidthMinPixels: 0,

    getPosition: (d) => [d.lon, d.lat],
    getRadius: () => 7,

    getFillColor: (d) => (d.compro ? COLOR_COMPRO : COLOR_NO_COMPRO),

    getLineColor: () => [0, 0, 0, 40],
    getLineWidth: () => 0.5,

    onHover: (info) => {
      onHover({
        object: (info.object as VentasCompro) ?? null,
        x: info.x,
        y: info.y,
      });
    },

    updateTriggers: {
      getFillColor: [data.length],
    },
  });
}
