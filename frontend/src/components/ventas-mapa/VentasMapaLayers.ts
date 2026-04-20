/**
 * Factory de layers deck.gl para el mapa de ventas.
 */
import { ScatterplotLayer } from '@deck.gl/layers';
import type { VentasCliente } from '../../types/ventas';
import type { VentasMetrica } from '../../types/ventas';
import {
  COLOR_SCALE_BURBUJAS,
  COLOR_SIN_VENTAS,
  interpolateColor,
  normalize,
  toRadius,
} from '../../lib/ventas-constants';

export interface HoverInfo {
  object: VentasCliente | null;
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
