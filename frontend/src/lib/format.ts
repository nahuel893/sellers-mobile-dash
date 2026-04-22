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

/**
 * Formatea un delta de puntos porcentuales.
 * null → '—', positive → '+X.Xpp', negative → '-X.Xpp' (always 1 decimal)
 */
export function fmtPctPp(delta: number | null): string {
  if (delta === null) return '—';
  const sign = delta >= 0 ? '+' : '';
  return `${sign}${delta.toFixed(1)}pp`;
}

/**
 * Formatea un ISO datetime en español corto.
 * Ejemplo: 'Lun 20 Abr · 14:32'
 * Capitaliza la primera letra del día de la semana, elimina puntos finales,
 * separa fecha y hora con ' · '.
 */
export function fmtDateShort(iso: string): string {
  const date = new Date(iso);
  const fmt = new Intl.DateTimeFormat('es-AR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
  const parts = fmt.formatToParts(date);

  let weekday = '';
  let day = '';
  let month = '';
  let hour = '';
  let minute = '';

  for (const part of parts) {
    switch (part.type) {
      case 'weekday': weekday = part.value.replace(/\.$/, ''); break;
      case 'day':     day = part.value; break;
      case 'month':   month = part.value.replace(/\.$/, ''); break;
      case 'hour':    hour = part.value; break;
      case 'minute':  minute = part.value; break;
    }
  }

  const weekdayCap = weekday.charAt(0).toUpperCase() + weekday.slice(1);
  const monthCap = month.charAt(0).toUpperCase() + month.slice(1);

  return `${weekdayCap} ${day} ${monthCap} · ${hour}:${minute}`;
}
