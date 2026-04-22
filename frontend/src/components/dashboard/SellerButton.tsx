
interface SellerButtonProps {
  /** 2-letter initials */
  iniciales: string;
  /** Full seller name (used in aria-label and tooltip) */
  nombre: string;
  /** Route identifier e.g. "Ruta 01" */
  ruta?: string | null;
  /** Currently selected */
  isActive: boolean;
  /** Casa Central variant — gradient lime→ok background */
  isCC?: boolean;
  onClick: () => void;
  onMouseEnter?: () => void;
}

/**
 * 36×36 seller avatar button for SellerRail.
 * Desktop: fixed left rail. Mobile: horizontal strip.
 */
export function SellerButton({
  iniciales,
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
        'relative flex items-center justify-center',
        'w-9 h-9 rounded-xl2 border transition-all duration-[180ms] cursor-pointer',
        'font-sans font-bold text-[11px] tracking-[0.03em]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lime',
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
        // Flex-shrink so rail doesn't compress buttons
        'flex-shrink-0',
      ].join(' ')}
      style={
        isCC
          ? { background: 'linear-gradient(135deg, oklch(0.86 0.18 115), oklch(0.78 0.16 145))' }
          : undefined
      }
      aria-label={`Ver avance de ${nombre}${ruta ? ` · ${ruta}` : ''}`}
      aria-pressed={isActive}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
    >
      {/* Active indicator bar:
          - xl (desktop): 3×20px bar at left:-13px (vertical rail)
          - <xl (mobile strip): 10×3px bar at bottom:-8px (horizontal strip)
      */}
      {isActive && !isCC && (
        <>
          {/* Desktop left bar (hidden on mobile) */}
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
          {/* Mobile bottom bar (hidden on desktop) */}
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

      {/* Initials */}
      <span className="relative z-10 leading-none">{iniciales}</span>

      {/* Tooltip */}
      <span
        className={[
          'pointer-events-none absolute z-50',
          'left-[calc(100%+12px)] top-1/2',
          '-translate-y-1/2 translate-x-[-4px]',
          'bg-bg-3 text-ink-0 border border-line-2 rounded-[6px]',
          'px-2.5 py-1.5 whitespace-nowrap',
          'opacity-0 transition-all duration-[180ms]',
          'shadow-[0_4px_12px_rgba(0,0,0,0.4)]',
          // Show on parent hover via sibling combinator not available in Tailwind → use group
          'group-hover:opacity-100 group-hover:translate-x-0',
        ].join(' ')}
        role="tooltip"
      >
        <span className="font-sans font-medium text-[11px] tracking-[-0.005em]">
          {nombre}
        </span>
        {ruta && (
          <span
            className="block font-mono text-ink-3 mt-[1px]"
            style={{ fontSize: 9, letterSpacing: '0.02em' }}
          >
            {ruta}
          </span>
        )}
      </span>
    </button>
  );
}
