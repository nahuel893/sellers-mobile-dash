/** Colores por grupo de marca (config.py:COLORES_GRUPO) */
export const BRAND_COLORS: Record<string, string> = {
  SALTA: '#1565C0',
  HEINEKEN: '#00A650',
  IMPERIAL: '#C8960C',
  MILLER: '#F9A825',
  MULTICERVEZAS: '#7B1FA2',
  IMPORTADAS: '#E65100',
};

/** Orden de visualización de marcas (config.py:GRUPOS_MARCA) */
export const BRAND_ORDER = ['SALTA', 'HEINEKEN', 'IMPERIAL', 'MILLER', 'MULTICERVEZAS', 'IMPORTADAS'] as const;

/** Categorías del dashboard (config.py:CATEGORIAS) */
export const CATEGORIES = ['CERVEZAS', 'MULTICCU', 'AGUAS_DANONE'] as const;
export type CategoryKey = (typeof CATEGORIES)[number];

/** Nombres para display (config.py:NOMBRES_CATEGORIA) */
export const CATEGORY_NAMES: Record<CategoryKey, string> = {
  CERVEZAS: 'Cervezas',
  MULTICCU: 'MultiCCU',
  AGUAS_DANONE: 'Aguas Danone',
};

/** Colores de performance (config.py) */
export const COLOR_GREEN = '#4CAF50';
export const COLOR_YELLOW = '#FFC107';
export const COLOR_RED = '#F44336';

/** Colores de marca */
export const COLOR_BRAND_DARK = '#1a1a2e';
export const COLOR_BRAND_DARK2 = '#16213e';
