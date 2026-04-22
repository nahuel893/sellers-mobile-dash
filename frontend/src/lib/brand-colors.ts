/** Brand → design token mapping (matches Phase A tokens: brand-{key}) */
export const BRAND_TO_TOKEN: Record<string, 'info' | 'ok' | 'warn' | 'lime' | 'violet' | 'danger'> = {
  SALTA: 'info',
  HEINEKEN: 'ok',
  IMPERIAL: 'warn',
  MILLER: 'lime',
  MULTICERVEZAS: 'violet',
  IMPORTADAS: 'danger',
};

/** Brand → Tailwind bg class for colored dot indicators */
export const BRAND_TO_DOT: Record<string, string> = {
  SALTA: 'bg-brand-info',
  HEINEKEN: 'bg-brand-ok',
  IMPERIAL: 'bg-brand-warn',
  MILLER: 'bg-brand-lime',
  MULTICERVEZAS: 'bg-brand-violet',
  IMPORTADAS: 'bg-brand-danger',
};

/**
 * Computes 2-letter initials from a full name.
 * - Two+ words → first letter of each of the first two words (uppercase)
 * - Single word → first two chars (uppercase)
 * - Empty / all whitespace → '??'
 */
export function computeInitials(nombre: string): string {
  if (!nombre || !nombre.trim()) return '??';
  const words = nombre.trim().split(/\s+/);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  const word = words[0];
  if (word.length < 2) return (word[0] + word[0]).toUpperCase();
  return word.slice(0, 2).toUpperCase();
}
