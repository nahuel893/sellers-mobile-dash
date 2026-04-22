import { SellerButton } from './SellerButton';
import type { Preventista } from '../../types/api';

interface SellerRailProps {
  preventistas: Preventista[];
  /** Currently active seller id (slug), or 'cc' for Casa Central */
  activeId: string;
  onSelect: (id: string) => void;
  /** Called on mouse-enter for prefetching */
  onPrefetch?: (id: string) => void;
}

const CC_PREVENTISTA: Preventista = {
  nombre: 'Casa Central',
  slug: 'cc',
  iniciales: 'CC',
  ruta: 'Agregado total',
};

/**
 * Seller navigation rail.
 * - xl (≥1280px): fixed left column, vertical
 * - below md (<768px): horizontal scrollable strip above hero
 * - md–xl: horizontal strip (same classes)
 */
export function SellerRail({ preventistas, activeId, onSelect, onPrefetch }: SellerRailProps) {
  return (
    <nav
      aria-label="Cambiar vendedor"
      className={[
        // Mobile / tablet — horizontal strip at top
        'flex flex-row flex-nowrap gap-2 overflow-x-auto',
        'px-4 py-2 border-b border-line',
        'scrollbar-none',
        // Desktop (xl) — fixed left rail, vertical
        'xl:flex-col xl:overflow-x-visible',
        'xl:fixed xl:left-3.5 xl:top-1/2 xl:-translate-y-1/2',
        'xl:px-2 xl:py-2.5 xl:gap-1.5',
        'xl:border-b-0',
        'xl:rounded-xl3',
        'xl:shadow-rail',
        // Rail background (desktop)
        'xl:border xl:border-line',
        'xl:backdrop-blur-rail',
      ].join(' ')}
      style={{
        // Applied only on xl via inline fallback — Tailwind doesn't support color-mix()
        // but we apply it via a CSS custom property approach
      }}
    >
      {/* "Equipo" vertical label (desktop only) */}
      <div
        className="hidden xl:block"
        style={{
          writingMode: 'vertical-rl',
          transform: 'rotate(180deg)',
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: 8,
          letterSpacing: '0.24em',
          color: 'var(--color-ink-3, #6a6353)',
          textTransform: 'uppercase',
          fontWeight: 600,
          paddingBottom: 4,
          marginBottom: 2,
          borderBottom: '1px dashed var(--color-line-2, #3a3527)',
        }}
        aria-hidden="true"
      >
        Equipo
      </div>

      {/* Casa Central */}
      <div className="group relative flex-shrink-0">
        <SellerButton
          iniciales={CC_PREVENTISTA.iniciales}
          nombre={CC_PREVENTISTA.nombre}
          ruta={CC_PREVENTISTA.ruta}
          isActive={activeId === 'cc'}
          isCC
          onClick={() => onSelect('cc')}
          onMouseEnter={() => onPrefetch?.('cc')}
        />
      </div>

      {/* Separator */}
      <div
        className="hidden xl:block self-stretch mx-auto bg-line"
        style={{ width: 16, height: 1, flexShrink: 0 }}
        aria-hidden="true"
      />
      <div
        className="xl:hidden h-full self-stretch bg-line"
        style={{ width: 1, minHeight: 20 }}
        aria-hidden="true"
      />

      {/* Preventista list */}
      {preventistas.map((p) => (
        <div key={p.slug} className="group relative flex-shrink-0">
          <SellerButton
            iniciales={p.iniciales}
            nombre={p.nombre}
            ruta={p.ruta}
            isActive={activeId === p.slug}
            onClick={() => onSelect(p.slug)}
            onMouseEnter={() => onPrefetch?.(p.slug)}
          />
        </div>
      ))}
    </nav>
  );
}
