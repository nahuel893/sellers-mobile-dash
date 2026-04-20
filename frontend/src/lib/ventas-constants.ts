/**
 * Constantes de negocio para el módulo Ventas Mapa.
 * Copiadas del PRD sección 5.
 */

// ---------------------------------------------------------------------------
// Tema oscuro
// ---------------------------------------------------------------------------

export const DARK = {
  bg: '#0f1117',
  card: '#1a1a2e',
  cardAlt: '#16213e',
  surface: '#252540',
  border: '#2d2d44',
  text: '#ffffff',
  textSecondary: '#a0a0b0',
  textMuted: '#6c6c7e',
  accentBlue: '#3498db',
  accentGreen: '#27ae60',
  accentRed: '#e74c3c',
  accentPurple: '#9b59b6',
  accentOrange: '#e67e22',
  accentYellow: '#f1c40f',
} as const;

// ---------------------------------------------------------------------------
// Escala de color de burbujas (azul → naranja → rojo)
// ---------------------------------------------------------------------------

export type ColorStop = { stop: number; color: [number, number, number] };

export const COLOR_SCALE_BURBUJAS: ColorStop[] = [
  { stop: 0.0, color: [70, 130, 180] },  // azul frío
  { stop: 0.5, color: [255, 165, 0] },   // naranja
  { stop: 1.0, color: [220, 20, 20] },   // rojo
];

export const COLOR_SCALE_CALOR: ColorStop[] = [
  { stop: 0.00, color: [0, 0, 150] },
  { stop: 0.15, color: [0, 100, 255] },
  { stop: 0.30, color: [0, 200, 255] },
  { stop: 0.45, color: [0, 255, 150] },
  { stop: 0.55, color: [200, 255, 0] },
  { stop: 0.70, color: [255, 200, 0] },
  { stop: 0.85, color: [255, 100, 0] },
  { stop: 1.00, color: [200, 0, 0] },
];

/** Threshold para colapsar badges de zonas (> N → una sola pill resumen) */
export const ZONE_BADGE_THRESHOLD = 5;

export const ZONE_COLORS: [number, number, number][] = [
  [255, 99, 132],
  [54, 162, 235],
  [255, 206, 86],
  [75, 192, 192],
  [153, 102, 255],
  [255, 159, 64],
  [199, 199, 199],
  [83, 102, 255],
  [255, 99, 255],
  [99, 255, 132],
];

// ---------------------------------------------------------------------------
// Escala de tamaño de burbujas (radio en píxeles)
// ---------------------------------------------------------------------------

export const ESCALA_FIJA_MAPA = {
  min: 3,   // radio mínimo (px) — nunca 0 para que sea visible
  max: 15,  // radio máximo (px)
} as const;

// ---------------------------------------------------------------------------
// Genéricos
// ---------------------------------------------------------------------------

/** Nunca aparecen en filtros ni en hover */
export const GENERICOS_EXCLUIDOS = [
  'ENVACES CCU',
  'AGUAS Y SODAS',
  'APERITIVOS',
  'DISPENSER',
  'ENVASES PALAU',
  'GASEOSA',
  'MARKETING BRANCA',
  'MARKETING',
] as const;

/** Siempre visibles en hover aunque tengan 0 ventas */
export const GENERICOS_HOVER_FIJOS = [
  'CERVEZAS',
  'AGUAS DANONE',
  'SIDRAS Y LICORES',
  'VINOS CCU',
  'FRATELLI B',
  'VINOS',
  'VINOS FINOS',
] as const;

// ---------------------------------------------------------------------------
// Mapa inicial
// ---------------------------------------------------------------------------

export const MAP_INITIAL_VIEW = {
  latitude: -24.78,
  longitude: -65.41,
  zoom: 11,
} as const;

/** Color para clientes sin ventas */
export const COLOR_SIN_VENTAS: [number, number, number] = [255, 0, 0];
export const COLOR_SIN_VENTAS_HALO: [number, number, number, number] = [255, 255, 255, 200];

// ---------------------------------------------------------------------------
// Utilidad: interpolar color de la escala
// ---------------------------------------------------------------------------

/**
 * Interpola un color RGB de la escala dado un valor t ∈ [0, 1].
 */
export function interpolateColor(
  t: number,
  scale: ColorStop[],
): [number, number, number] {
  const clamped = Math.max(0, Math.min(1, t));

  for (let i = 0; i < scale.length - 1; i++) {
    const lo = scale[i];
    const hi = scale[i + 1];
    if (clamped >= lo.stop && clamped <= hi.stop) {
      const range = hi.stop - lo.stop;
      const f = range === 0 ? 0 : (clamped - lo.stop) / range;
      return [
        Math.round(lo.color[0] + f * (hi.color[0] - lo.color[0])),
        Math.round(lo.color[1] + f * (hi.color[1] - lo.color[1])),
        Math.round(lo.color[2] + f * (hi.color[2] - lo.color[2])),
      ];
    }
  }

  return scale[scale.length - 1].color;
}

/**
 * Normaliza un valor al rango [min, max] → [0, 1].
 * Si min === max (todos iguales) devuelve 0.5 para el color medio.
 */
export function normalize(value: number, min: number, max: number): number {
  if (max === min) return 0.5;
  return Math.max(0, Math.min(1, (value - min) / (max - min)));
}

/**
 * Mapea un valor normalizado (0-1) al radio de la burbuja.
 */
export function toRadius(t: number): number {
  return ESCALA_FIJA_MAPA.min + t * (ESCALA_FIJA_MAPA.max - ESCALA_FIJA_MAPA.min);
}
