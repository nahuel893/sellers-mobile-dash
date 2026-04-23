import { useState } from 'react';
import { SellerButton } from './SellerButton';
import { toSlug } from '../../lib/format';
import { useSupervisores } from '../../hooks/use-supervisores';
import { useVendedoresPorSupervisor } from '../../hooks/use-vendedores';
import type { Preventista } from '../../types/api';

interface SellerRailProps {
  /** All preventistas (used by mobile strip + desktop supervisor→preventista resolution) */
  preventistas: Preventista[];
  /** Currently active node id — 'cc' | 'sup:<slug>' | '<vendedorSlug>' */
  activeId: string;
  /** Called with the new id (route change) */
  onSelect: (id: string) => void;
  /** Called on mouseenter for prefetching. Receives the same id shape as onSelect. */
  onPrefetch?: (id: string) => void;
}

const ROOT_LABEL = 'GFARAH';

/** Map supervisor → preventistas.iniciales/ruta from the full preventistas list. */
function findPreventista(
  list: Preventista[],
  nombre: string,
): Preventista | undefined {
  const slug = toSlug(nombre);
  return list.find((p) => p.slug === slug);
}

/**
 * Seller navigation rail.
 * - xl (≥1280px): hover-reveal tree — Root → Supervisores → Preventistas (3 columns)
 * - <xl: horizontal scrollable strip (flat: root + all preventistas), legacy layout
 */
export function SellerRail({ preventistas, activeId, onSelect, onPrefetch }: SellerRailProps) {
  return (
    <>
      {/* Mobile / tablet: flat horizontal strip (unchanged, awaiting later iteration) */}
      <MobileStrip
        preventistas={preventistas}
        activeId={activeId}
        onSelect={onSelect}
        onPrefetch={onPrefetch}
      />

      {/* Desktop: hover-reveal tree */}
      <DesktopTree
        preventistas={preventistas}
        activeId={activeId}
        onSelect={onSelect}
        onPrefetch={onPrefetch}
      />
    </>
  );
}

// ---------------------------------------------------------------------------
// Mobile / tablet strip (hierarchical drilldown)
// ---------------------------------------------------------------------------

type MobileLevel = 'root' | 'supervisors' | 'preventistas';

function MobileStrip({ preventistas, activeId, onSelect, onPrefetch }: SellerRailProps) {
  const [level, setLevel] = useState<MobileLevel>('root');
  const [supName, setSupName] = useState<string | null>(null);

  const { data: supervisores = [], isLoading: isLoadingSup } = useSupervisores('1');
  const { data: vendedoresDelSup = [], isLoading: isLoadingVen } =
    useVendedoresPorSupervisor(supName, '1');

  const activeSupSlug = activeId.startsWith('sup:') ? activeId.slice(4) : null;

  const goBack = () => {
    if (level === 'preventistas') setLevel('supervisors');
    else if (level === 'supervisors') setLevel('root');
  };

  // Breadcrumb taps — navigate AND drill-in (as if tapping the pill itself)
  const jumpToRoot = () => {
    onSelect('cc');
    setLevel('supervisors');
  };

  return (
    <div className="xl:hidden flex flex-col border-b border-line">
      {/* Breadcrumb header — only shown when drilled down */}
      {level !== 'root' && (
        <div
          className="flex items-center gap-2 px-4 pt-2 pb-1 text-ink-2"
          style={{ fontSize: 11, letterSpacing: '0.02em' }}
        >
          <button
            type="button"
            onClick={goBack}
            aria-label="Volver un nivel"
            className="flex items-center justify-center w-6 h-6 rounded-md border border-line text-ink-0
                       hover:border-line-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lime"
          >
            ←
          </button>
          <nav aria-label="Ruta de navegación" className="flex items-center gap-1 flex-wrap">
            <button
              type="button"
              onClick={jumpToRoot}
              className="font-sans font-medium hover:text-ink-0 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-lime rounded"
            >
              {ROOT_LABEL}
            </button>
            {level === 'preventistas' && supName && (
              <>
                <span aria-hidden="true" className="text-ink-3">›</span>
                <span className="font-sans font-medium text-ink-0">{supName}</span>
              </>
            )}
          </nav>
        </div>
      )}

      {/* Strip */}
      <nav
        aria-label="Cambiar vendedor"
        className="flex flex-row flex-nowrap gap-2 overflow-x-auto px-4 py-2 scrollbar-none"
      >
        {level === 'root' && (
          <div className="flex-shrink-0">
            <SellerButton
              nombre={ROOT_LABEL}
              ruta="Agregado total"
              isActive={activeId === 'cc'}
              isCC
              onClick={() => {
                onSelect('cc');
                setLevel('supervisors');
              }}
              onMouseEnter={() => onPrefetch?.('cc')}
            />
          </div>
        )}

        {level === 'supervisors' && (
          <>
            {isLoadingSup && <InlineHint>Cargando…</InlineHint>}
            {!isLoadingSup && supervisores.length === 0 && (
              <InlineHint>Sin supervisores</InlineHint>
            )}
            {supervisores.map((sup) => {
              const slug = toSlug(sup);
              const id = 'sup:' + slug;
              return (
                <div key={sup} className="flex-shrink-0">
                  <SellerButton
                    nombre={sup}
                    isActive={activeSupSlug === slug}
                    onClick={() => {
                      onSelect(id);
                      setSupName(sup);
                      setLevel('preventistas');
                    }}
                    onMouseEnter={() => onPrefetch?.(id)}
                  />
                </div>
              );
            })}
          </>
        )}

        {level === 'preventistas' && (
          <>
            {isLoadingVen && <InlineHint>Cargando…</InlineHint>}
            {!isLoadingVen && vendedoresDelSup.length === 0 && (
              <InlineHint>Sin preventistas</InlineHint>
            )}
            {vendedoresDelSup.map((vendedorName) => {
              const vSlug = toSlug(vendedorName);
              const pv = findPreventista(preventistas, vendedorName);
              return (
                <div key={vendedorName} className="flex-shrink-0">
                  <SellerButton
                    nombre={vendedorName}
                    ruta={pv?.ruta}
                    isActive={activeId === vSlug}
                    onClick={() => onSelect(vSlug)}
                    onMouseEnter={() => onPrefetch?.(vSlug)}
                  />
                </div>
              );
            })}
          </>
        )}
      </nav>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Desktop tree (hover-reveal flyout — 3 columns)
// ---------------------------------------------------------------------------

function DesktopTree({ preventistas, activeId, onSelect, onPrefetch }: SellerRailProps) {
  const [expandedRoot, setExpandedRoot] = useState(false);
  const [hoveredSup, setHoveredSup] = useState<string | null>(null);

  const { data: supervisores = [], isLoading: isLoadingSup, error: supError } =
    useSupervisores('1');
  const { data: vendedoresDelSup = [], isLoading: isLoadingVen } =
    useVendedoresPorSupervisor(hoveredSup, '1');

  const closeAll = () => {
    setExpandedRoot(false);
    setHoveredSup(null);
  };

  const activeSupSlug = activeId.startsWith('sup:') ? activeId.slice(4) : null;

  return (
    <div
      className="hidden xl:flex xl:fixed xl:left-0 xl:flex-row xl:gap-1 xl:items-start z-50"
      // Vertical position: centered on the root pill (≈34px from its own center),
      // NOT on the full tree bounding box — avoids "jumping" when cols 2/3 expand.
      style={{ top: 'calc(50vh - 34px)' }}
      onMouseLeave={closeAll}
    >
      {/* Col 1: root (always visible) */}
      <nav
        aria-label="Cambiar vendedor"
        className="flex flex-col px-1 py-1.5 gap-1 rounded-xl3 shadow-rail border border-line backdrop-blur-rail"
      >
        <VerticalLabel>Equipo</VerticalLabel>

        <div onMouseEnter={() => setExpandedRoot(true)}>
          <SellerButton
            nombre={ROOT_LABEL}
            ruta="Agregado total"
            isActive={activeId === 'cc'}
            isCC
            onClick={() => onSelect('cc')}
            onMouseEnter={() => onPrefetch?.('cc')}
          />
        </div>
      </nav>

      {/* Col 2: supervisores (visible when root hovered) */}
      {expandedRoot && (
        <nav
          aria-label="Supervisores"
          className="flex flex-col px-1 py-1.5 gap-1 rounded-xl3 shadow-rail border border-line backdrop-blur-rail max-h-[90vh] overflow-y-auto"
        >
          <ColumnHeader>Supervisores</ColumnHeader>
          {isLoadingSup && <EmptyHint>Cargando…</EmptyHint>}
          {!isLoadingSup && supError && <EmptyHint>Error al cargar</EmptyHint>}
          {!isLoadingSup && !supError && supervisores.length === 0 && (
            <EmptyHint>Sin supervisores</EmptyHint>
          )}
          {supervisores.map((sup) => {
            const supSlug = toSlug(sup);
            const supId = 'sup:' + supSlug;
            return (
              <div
                key={sup}
                onMouseEnter={() => {
                  setHoveredSup(sup);
                  onPrefetch?.(supId);
                }}
              >
                <SellerButton
                  nombre={sup}
                  isActive={activeSupSlug === supSlug}
                  onClick={() => onSelect(supId)}
                />
              </div>
            );
          })}
        </nav>
      )}

      {/* Col 3: preventistas del supervisor hovered */}
      {expandedRoot && hoveredSup && (
        <nav
          aria-label={`Preventistas de ${hoveredSup}`}
          className="flex flex-col px-1 py-1.5 gap-1 rounded-xl3 shadow-rail border border-line backdrop-blur-rail max-h-[90vh] overflow-y-auto"
        >
          <ColumnHeader>Preventistas</ColumnHeader>
          {isLoadingVen && <EmptyHint>Cargando…</EmptyHint>}
          {!isLoadingVen && vendedoresDelSup.length === 0 && (
            <EmptyHint>Sin preventistas</EmptyHint>
          )}
          {vendedoresDelSup.map((vendedorName) => {
            const vSlug = toSlug(vendedorName);
            const pv = findPreventista(preventistas, vendedorName);
            return (
              <div
                key={vendedorName}
                onMouseEnter={() => onPrefetch?.(vSlug)}
              >
                <SellerButton
                  nombre={vendedorName}
                  ruta={pv?.ruta}
                  isActive={activeId === vSlug}
                  onClick={() => onSelect(vSlug)}
                />
              </div>
            );
          })}
        </nav>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

function VerticalLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
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
      {children}
    </div>
  );
}

function ColumnHeader({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="text-ink-3 font-sans font-semibold uppercase px-2 py-1"
      style={{ fontSize: 9, letterSpacing: '0.18em' }}
      aria-hidden="true"
    >
      {children}
    </div>
  );
}

function EmptyHint({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="text-ink-3 font-sans px-2 py-2 italic"
      style={{ fontSize: 10 }}
    >
      {children}
    </div>
  );
}

/** Inline hint for mobile horizontal strip (same row as pills) */
function InlineHint({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="flex items-center text-ink-3 font-sans px-3 italic h-9"
      style={{ fontSize: 11 }}
    >
      {children}
    </div>
  );
}
