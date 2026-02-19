import { COLOR_GREEN, COLOR_YELLOW, COLOR_RED } from './constants';

/** Número con separador de miles español: 1234567 → "1.234.567" */
export function fmtNum(n: number): string {
  return Math.round(n).toLocaleString('es-AR');
}

/** Color según % tendencia vs cupo (config.py:color_por_rendimiento) */
export function colorByPerformance(pct: number): string {
  if (pct >= 80) return COLOR_GREEN;
  if (pct >= 70) return COLOR_YELLOW;
  return COLOR_RED;
}

/** Fecha en español: "Jueves, 19 de febrero de 2026" */
export function formatDateSpanish(isoDate: string): string {
  const date = new Date(isoDate + 'T12:00:00');
  const days = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
  const months = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
  ];
  const dayName = days[date.getDay()];
  const monthName = months[date.getMonth()];
  const str = `${dayName}, ${date.getDate()} de ${monthName} de ${date.getFullYear()}`;
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/** Convierte nombre a slug URL-safe (views.py:to_slug) */
export function toSlug(name: string): string {
  return name.trim().replace(/-/g, '%2D').replace(/ /g, '-');
}

/** Convierte slug a nombre (views.py:from_slug) */
export function fromSlug(slug: string): string {
  return decodeURIComponent(slug.replace(/-/g, ' '));
}
