import type { ReactNode } from 'react';

interface NavItem {
  key: string;
  label: string;
  icon: ReactNode;
  isActive?: boolean;
}

/** Simple SVG icons — no external dependency */
const Icons = {
  Inicio: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M3 10L10 3L17 10V17H13V12H7V17H3V10Z" fill="currentColor" opacity={0.9} />
    </svg>
  ),
  Avance: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="2" fill="none" />
      <path d="M10 10L10 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M10 10L14 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  Equipo: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="8" cy="7" r="3" stroke="currentColor" strokeWidth="1.5" fill="none" />
      <path d="M2 17c0-3 2.7-5 6-5s6 2 6 5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      <circle cx="15" cy="6" r="2.5" stroke="currentColor" strokeWidth="1.5" fill="none" />
      <path d="M13 15c.5-2 1.8-3 3.5-3" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
    </svg>
  ),
  Ajustes: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="2.5" stroke="currentColor" strokeWidth="1.5" fill="none" />
      <path
        d="M10 2v2M10 16v2M2 10h2M16 10h2M4.2 4.2l1.4 1.4M14.4 14.4l1.4 1.4M14.4 5.6l1.4-1.4M4.2 15.8l1.4-1.4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  ),
};

interface BottomNavProps {
  /** Active item key */
  activeKey?: string;
  onNavigate?: (key: string) => void;
}

const NAV_ITEMS: Pick<NavItem, 'key' | 'label'>[] = [
  { key: 'inicio',  label: 'Inicio'  },
  { key: 'avance',  label: 'Avance'  },
  { key: 'equipo',  label: 'Equipo'  },
  { key: 'ajustes', label: 'Ajustes' },
];

/**
 * Mobile-only bottom navigation bar.
 * Hidden at md breakpoint and above (md:hidden).
 */
export function BottomNav({ activeKey = 'avance', onNavigate }: BottomNavProps) {
  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-50
                 bg-bg-1 border-t border-line h-[72px]
                 flex items-center justify-around px-2"
      aria-label="Navegación principal"
    >
      {NAV_ITEMS.map(({ key, label }) => {
        const isActive = activeKey === key;
        const icon = Icons[label as keyof typeof Icons];

        return (
          <button
            key={key}
            type="button"
            className={[
              'flex flex-col items-center gap-1 px-3 py-1.5 rounded-xl',
              'transition-colors duration-150 cursor-pointer border-0 bg-transparent',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lime',
              isActive ? 'text-ink-0' : 'text-ink-3 hover:text-ink-2',
            ].join(' ')}
            aria-current={isActive ? 'page' : undefined}
            onClick={() => onNavigate?.(key)}
          >
            {icon}
            <span
              className="font-sans"
              style={{ fontSize: 10, fontWeight: isActive ? 600 : 500, letterSpacing: '0.02em' }}
            >
              {label}
            </span>

            {/* Active dot indicator */}
            {isActive && (
              <span
                className="absolute bottom-2 w-1 h-1 rounded-full bg-lime"
                aria-hidden="true"
              />
            )}
          </button>
        );
      })}
    </nav>
  );
}
