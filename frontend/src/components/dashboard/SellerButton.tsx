
/** Title-case a name, handling ALL-CAPS DB values and words with hyphens. */
function toTitleCase(s: string): string {
  if (!s) return '';
  return s
    .toLowerCase()
    .replace(/(^|[\s\-/])([a-záéíóúñü])/g, (_, sep: string, ch: string) => sep + ch.toUpperCase());
}

interface SellerButtonProps {
  /** Full seller name (shown on the pill; truncated if overflow) */
  nombre: string;
  /** Route identifier e.g. "Ruta 01" (used in aria-label only) */
  ruta?: string | null;
  /** Currently selected */
  isActive: boolean;
  /** Casa Central variant — gradient lime→ok background */
  isCC?: boolean;
  onClick: () => void;
  onMouseEnter?: () => void;
}

/**
 * Seller pill for SellerRail.
 * Desktop (xl): vertical rail, fixed width. Mobile: horizontal scroll strip.
 * Shows full lowercase name in 10px; truncates if overflow (full name on hover title).
 */
export function SellerButton({
  nombre,
  ruta,
  isActive,
  isCC = false,
  onClick,
  onMouseEnter,
}: SellerButtonProps) {
  return (
    <button
      type="button"
      className={[
        'relative flex items-center',
        'h-9 px-3 rounded-xl2 border transition-all duration-[180ms] cursor-pointer',
        'font-sans font-medium text-[10px] leading-tight tracking-[-0.005em]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lime',
        'flex-shrink-0',
        // Width: 1/3 narrower than previous pass — mobile 96, desktop 116
        'w-[96px] xl:w-[116px]',
        // Base state
        !isActive && !isCC
          ? 'bg-bg-2 border-line text-ink-2 hover:text-ink-0 hover:border-line-2 hover:translate-x-0.5'
          : '',
        // Active (non-CC)
        isActive && !isCC
          ? 'bg-ink-0 text-bg-0 border-ink-0'
          : '',
        // CC variant (inactive)
        isCC && !isActive
          ? 'border-transparent text-bg-0'
          : '',
        // CC active
        isCC && isActive
          ? 'outline outline-2 outline-ink-0 outline-offset-2 border-transparent text-bg-0'
          : '',
      ].join(' ')}
      style={
        isCC
          ? { background: 'linear-gradient(135deg, oklch(0.86 0.18 115), oklch(0.78 0.16 145))' }
          : undefined
      }
      aria-label={`Ver avance de ${nombre}${ruta ? ` · ${ruta}` : ''}`}
      aria-pressed={isActive}
      title={toTitleCase(nombre)}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
    >
      {/* Active indicator bar:
          - xl (desktop): 3×20 bar at left:-13 (vertical rail)
          - <xl (mobile strip): 10×3 bar at bottom:-8 (horizontal strip)
      */}
      {isActive && !isCC && (
        <>
          {/* Desktop left bar */}
          <span
            className="hidden xl:block absolute rounded-sm bg-lime"
            style={{
              left: -13,
              top: '50%',
              transform: 'translateY(-50%)',
              width: 3,
              height: 20,
              boxShadow: '0 0 8px oklch(0.86 0.18 115)',
            }}
            aria-hidden="true"
          />
          {/* Mobile bottom bar */}
          <span
            className="xl:hidden absolute rounded-sm bg-lime"
            style={{
              bottom: -8,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 10,
              height: 3,
              boxShadow: '0 0 6px oklch(0.86 0.18 115)',
            }}
            aria-hidden="true"
          />
        </>
      )}

      {/* Name — truncate to avoid overflow; full name in `title` attr for hover */}
      <span className="relative z-10 truncate w-full text-left">
        {toTitleCase(nombre)}
      </span>
    </button>
  );
}
