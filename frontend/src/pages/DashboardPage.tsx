import { useState, useEffect, useRef, useMemo } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useQueryClient } from '@tanstack/react-query';

import { slideVariants } from '../lib/dashboard-transitions';
import { api } from '../lib/api-client';

import { SellerRail } from '../components/dashboard/SellerRail';
import { TopBar } from '../components/dashboard/TopBar';
import { HeroCard } from '../components/dashboard/HeroCard';
import { GenericBlock } from '../components/dashboard/GenericBlock';
import { BrandGrid } from '../components/dashboard/BrandGrid';
import { StatsStrip } from '../components/dashboard/StatsStrip';
import { WeatherWidget } from '../components/dashboard/WeatherWidget';
import { BottomNav } from '../components/dashboard/BottomNav';

import { usePreventistas } from '../hooks/use-preventistas';
import { useVendedor } from '../hooks/use-vendedor';
import { useSupervisor } from '../hooks/use-supervisor';
import { useSucursal } from '../hooks/use-sucursal';
import { useAvanceSparkline } from '../hooks/use-avance-sparkline';
import { useAvanceDelta } from '../hooks/use-avance-delta';
import { useDiasHabiles } from '../hooks/use-dias-habiles';
import { useKeyboardNav } from '../hooks/use-keyboard-nav';

import type { BrandCardProps } from '../components/dashboard/BrandCard';
import type { GenericBlockProps } from '../components/dashboard/GenericBlock';
import type { CategoryData } from '../types/api';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GENERICS_KEY = 'GENERICOS';
const ROOT_LABEL = 'GFARAH';
const SUPERVISOR_PREFIX = 'sup:';

/** Presentational config for each generic category block */
const GENERIC_CATEGORIES = [
  {
    key: 'AGUAS_DANONE',
    title: 'Aguas Danone',
    eyebrow: 'Genérico',
    caption: 'Aguas',
  },
  {
    key: 'MULTICCU',
    title: 'MultiCCU',
    eyebrow: 'Grupo de genéricos',
    caption: 'Vinos CCU · Sidras · Licores',
  },
] as const;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Derive HeroCard props from a CategoryData + dias context.
 * Returns null when data is not yet available.
 */
function heroPropsFromCategory(
  categoryData: CategoryData | undefined,
  sellerName: string,
  eyebrow: string,
  ruta: string | null | undefined,
  iniciales: string | undefined,
  daysElapsedPct: number,
  daysRemaining: number,
) {
  if (!categoryData) return null;

  const { resumen } = categoryData;
  const pct = resumen.pct_tendencia ?? 0;
  const vendido = resumen.ventas ?? 0;
  const cupo = resumen.cupo ?? 0;
  const falta = resumen.falta ?? 0;
  const tendencia = resumen.tendencia ?? 0;
  const gap = tendencia - cupo;

  // Vta/día req: falta / max(daysRemaining, 1)
  const diasRestantesEff = Math.max(daysRemaining, 1);
  const ventaDiaRequerida = falta / diasRestantesEff;

  // Ritmo requerido for TrendRow: (falta / cupo) * 100 expressed as pct
  // Actually: pct we need to close per remaining day → tendencia pct / total days × remaining
  const ritmoRequerido = cupo > 0 ? (falta / cupo) * 100 : 0;

  return {
    eyebrow,
    title: sellerName,
    ruta,
    iniciales,
    pct,
    vendido,
    cupo,
    falta,
    ventaDiaRequerida,
    daysElapsedPct,
    daysRemaining,
    tendencia,
    gap,
    ritmoRequerido,
    showWeather: true,
  };
}

/**
 * Derive GenericBlock props from a CategoryData.
 * Returns null when data is not yet available.
 */
function genericBlockPropsFromCategory(
  categoryData: CategoryData | undefined,
  title: string,
  eyebrow: string,
  caption: string,
  daysElapsedPct: number,
  daysRemaining: number,
): GenericBlockProps | null {
  if (!categoryData) return null;

  const { resumen } = categoryData;
  const pct = resumen.pct_tendencia ?? 0;
  const vendido = resumen.ventas ?? 0;
  const cupo = resumen.cupo ?? 0;
  const falta = resumen.falta ?? 0;
  const tendencia = resumen.tendencia ?? 0;
  const gap = tendencia - cupo;

  const diasRestantesEff = Math.max(daysRemaining, 1);
  const ventaDiaRequerida = falta / diasRestantesEff;
  const ritmoRequerido = cupo > 0 ? (falta / cupo) * 100 : 0;

  return {
    eyebrow,
    title,
    caption,
    pct,
    vendido,
    cupo,
    falta,
    ventaDiaRequerida,
    daysElapsedPct,
    daysRemaining,
    tendencia,
    gap,
    ritmoRequerido,
  };
}

// ---------------------------------------------------------------------------
// Skeletons
// ---------------------------------------------------------------------------

function HeroSkeleton() {
  return (
    <div className="border border-line rounded-[18px] p-7 animate-pulse space-y-5"
         style={{ background: '#17150f' }}>
      <div className="flex justify-between items-start">
        <div className="space-y-2">
          <div className="h-2 w-16 bg-white/10 rounded" />
          <div className="h-5 w-36 bg-white/10 rounded" />
        </div>
        <div className="h-7 w-24 bg-white/10 rounded-md" />
      </div>
      <div className="flex items-center gap-6">
        <div className="h-[180px] w-[180px] bg-white/10 rounded-full flex-shrink-0" />
        <div className="flex flex-col gap-4 flex-1">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="flex justify-between">
              <div className="h-2 w-14 bg-white/10 rounded" />
              <div className="h-4 w-16 bg-white/10 rounded" />
            </div>
          ))}
        </div>
      </div>
      <div className="h-3 w-full bg-white/10 rounded" />
      <div className="grid grid-cols-2 gap-3">
        <div className="h-16 bg-white/10 rounded-xl" />
        <div className="h-16 bg-white/10 rounded-xl" />
      </div>
    </div>
  );
}

function BrandGridSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 animate-pulse">
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="bg-bg-1 border border-line rounded-[14px] p-[18px] space-y-3">
          <div className="flex justify-between">
            <div className="h-3 w-20 bg-white/10 rounded" />
            <div className="h-3 w-8 bg-white/10 rounded" />
          </div>
          <div className="h-10 w-24 bg-white/10 rounded" />
          <div className="h-2 w-full bg-white/10 rounded" />
          <div className="grid grid-cols-3 gap-2 pt-3">
            {[0, 1, 2].map((j) => (
              <div key={j} className="space-y-1">
                <div className="h-2 w-10 bg-white/10 rounded" />
                <div className="h-4 w-14 bg-white/10 rounded" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// DashboardPage
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  // ── Seller selection ──────────────────────────────────────────────────────
  const [sellerId, setSellerId] = useState<string>('cc');
  const [activeCategory, setActiveCategory] = useState<string>('CERVEZAS');
  const directionRef = useRef<1 | -1>(1);
  const [syncedAt] = useState<Date>(new Date());

  // Restore from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('preventista_sel');
    if (saved) setSellerId(saved);
  }, []);

  // Persist to localStorage on every change
  useEffect(() => {
    localStorage.setItem('preventista_sel', sellerId);
  }, [sellerId]);

  // ── Data ──────────────────────────────────────────────────────────────────
  const { data: preventistas = [] } = usePreventistas(1);
  const { data: diasHabiles } = useDiasHabiles();

  // ── Selection kind derived from sellerId shape ───────────────────────────
  const isRoot = sellerId === 'cc';
  const isSup = sellerId.startsWith(SUPERVISOR_PREFIX);
  const supSlug = isSup ? sellerId.slice(SUPERVISOR_PREFIX.length) : undefined;
  const venSlug = !isRoot && !isSup ? sellerId : undefined;

  // Fallback: if saved sellerId is a vendedor no longer in the list, reset to root
  useEffect(() => {
    if (isRoot || isSup) return;
    if (preventistas.length > 0 && !preventistas.find((p) => p.slug === sellerId)) {
      setSellerId('cc');
    }
  }, [preventistas, sellerId, isRoot, isSup]);

  // All sellers in order (cc first, then list) — supervisors are reached via tree, not arrows
  const allIds = useMemo(() => ['cc', ...preventistas.map((p) => p.slug)], [preventistas]);
  // ── Keyboard nav ──────────────────────────────────────────────────────────
  const switchTo = (id: string) => {
    const oldIdx = allIds.indexOf(sellerId);
    const newIdx = allIds.indexOf(id);
    directionRef.current = newIdx >= oldIdx ? 1 : -1;
    setSellerId(id);
  };

  const prevId = () => {
    if (allIds.length === 0) return sellerId;
    const idx = allIds.indexOf(sellerId);
    if (idx === -1) return 'cc'; // supervisor selected → arrows jump to root
    return allIds[(idx - 1 + allIds.length) % allIds.length];
  };

  const nextId = () => {
    if (allIds.length === 0) return sellerId;
    const idx = allIds.indexOf(sellerId);
    if (idx === -1) return 'cc';
    return allIds[(idx + 1) % allIds.length];
  };

  useKeyboardNav({
    onPrev: () => switchTo(prevId()),
    onNext: () => switchTo(nextId()),
    enabled: true,
  });

  // ── Seller-specific data ─────────────────────────────────────────────────
  // Root → useSucursal('1'), supervisor → useSupervisor(slug), vendedor → useVendedor(slug)
  const { data: sucursalData, isLoading: isLoadingSucursal } = useSucursal(
    isRoot ? '1' : undefined,
  );
  const { data: supervisorData, isLoading: isLoadingSupervisor } = useSupervisor(
    supSlug,
    '1',
  );
  const { data: vendedorData, isLoading: isLoadingVendedor } = useVendedor(venSlug);

  const isLoading = isRoot
    ? isLoadingSucursal
    : isSup
      ? isLoadingSupervisor
      : isLoadingVendedor;

  // Raw categories for active seller
  const categories: Record<string, CategoryData> | undefined = isRoot
    ? sucursalData?.categories
    : isSup
      ? supervisorData?.categories
      : vendedorData?.categories;

  // Active category data
  const categoryData = categories?.[activeCategory];

  // ── Current seller metadata ───────────────────────────────────────────────
  const currentPreventista = preventistas.find((p) => p.slug === sellerId);
  const currentSellerName = isRoot
    ? ROOT_LABEL
    : isSup
      ? (supervisorData?.nombre ?? supSlug!)
      : (currentPreventista?.nombre ?? sellerId);

  // ── Sparkline + Delta ─────────────────────────────────────────────────────
  // Root keeps the legacy 'casa-central' slug; supervisor/vendedor use their own slug.
  const effectiveSlug = isRoot ? 'casa-central' : isSup ? supSlug! : sellerId;
  // GENERICOS layout has no brand grid → no sparkline/delta needed.
  // Fall back to 'CERVEZAS' to keep the cache warm for the next tab switch.
  const sparklineCat = activeCategory === GENERICS_KEY ? 'CERVEZAS' : activeCategory;
  const { data: sparklineData } = useAvanceSparkline(effectiveSlug, 18, sparklineCat);
  const { data: deltaData } = useAvanceDelta(effectiveSlug, sparklineCat);

  // ── Days elapsed pct ──────────────────────────────────────────────────────
  const daysElapsedPct = diasHabiles
    ? Math.round((diasHabiles.transcurridos / Math.max(diasHabiles.habiles, 1)) * 100)
    : 0;
  const daysRemaining = diasHabiles?.restantes ?? 0;

  // ── Hero props ────────────────────────────────────────────────────────────
  const heroEyebrow = isRoot ? 'Sucursal' : isSup ? 'Supervisor' : 'Vendedor';
  const heroRuta = isRoot
    ? 'Agregado total'
    : isSup
      ? null
      : (currentPreventista?.ruta ?? null);
  const heroIniciales = isRoot
    ? 'GF'
    : isSup
      ? undefined
      : currentPreventista?.iniciales;

  const heroProps = useMemo(
    () =>
      heroPropsFromCategory(
        categoryData,
        currentSellerName,
        heroEyebrow,
        heroRuta,
        heroIniciales,
        daysElapsedPct,
        daysRemaining,
      ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [categoryData, currentSellerName, sellerId, daysElapsedPct, daysRemaining],
  );

  // ── GenericBlock props (AGUAS_DANONE + MULTICCU) ─────────────────────────
  const genericBlocksProps = useMemo(
    () =>
      GENERIC_CATEGORIES.map((cat) => ({
        key: cat.key,
        props: genericBlockPropsFromCategory(
          categories?.[cat.key],
          cat.title,
          cat.eyebrow,
          cat.caption,
          daysElapsedPct,
          daysRemaining,
        ),
      })),
    [categories, daysElapsedPct, daysRemaining],
  );

  // ── BrandCard props ───────────────────────────────────────────────────────
  const brandCards: BrandCardProps[] = useMemo(() => {
    if (!categoryData) return [];

    const datos = categoryData.datos.filter((d) => d.grupo_marca !== null);
    // Sort by pct desc for rank
    const sorted = [...datos].sort((a, b) => b.pct_tendencia - a.pct_tendencia);

    return sorted.map((marca, idx) => {
      // Build sparkline points for this grupo_marca
      const grupoKey = marca.grupo_marca!;
      const points: number[] =
        sparklineData?.puntos.map((p) => p.por_grupo[grupoKey] ?? 0) ?? [];

      // Delta pp
      const deltaEntry = deltaData?.deltas.find((d) => d.grupo_marca === grupoKey);
      const deltaPp = deltaEntry?.delta_pp ?? null;

      const diasRestantesEff = Math.max(daysRemaining, 1);
      const ventaDiaRequerida = marca.falta / diasRestantesEff;

      return {
        grupoMarca: grupoKey,
        pct: marca.pct_tendencia,
        deltaPp,
        vendido: marca.ventas,
        cupo: marca.cupo,
        falta: marca.falta,
        ventaDiaRequerida,
        rank: idx + 1,
        sparklinePoints: points,
        daysElapsedPct,
      } satisfies BrandCardProps;
    });
  }, [categoryData, sparklineData, deltaData, daysElapsedPct, daysRemaining]);

  // For StatsStrip
  const brandStats = useMemo(
    () => brandCards.map((c) => ({ grupoMarca: c.grupoMarca, pct: c.pct })),
    [brandCards],
  );

  // ── Prefetch adjacent sellers ─────────────────────────────────────────────
  const queryClient = useQueryClient();

  const handlePrefetch = (id: string) => {
    const prefetchSlug =
      id === 'cc'
        ? 'casa-central'
        : id.startsWith(SUPERVISOR_PREFIX)
          ? id.slice(SUPERVISOR_PREFIX.length)
          : id;

    queryClient.prefetchQuery({
      queryKey: ['sparkline', prefetchSlug, 18, sparklineCat],
      queryFn: () => api.getSparkline(prefetchSlug, 18, sparklineCat),
      staleTime: 5 * 60 * 1000,
    });
    queryClient.prefetchQuery({
      queryKey: ['delta', prefetchSlug, sparklineCat],
      queryFn: () => api.getDelta(prefetchSlug, sparklineCat),
      staleTime: 5 * 60 * 1000,
    });

    // Prefetch detail endpoint based on node kind
    if (id.startsWith(SUPERVISOR_PREFIX)) {
      const supSlugToFetch = id.slice(SUPERVISOR_PREFIX.length);
      queryClient.prefetchQuery({
        queryKey: ['supervisor', supSlugToFetch, '1'],
        queryFn: () => api.getSupervisor(supSlugToFetch, '1'),
        staleTime: 5 * 60 * 1000,
      });
    } else if (id !== 'cc') {
      queryClient.prefetchQuery({
        queryKey: ['vendedor', id],
        queryFn: () => api.getVendedor(id),
        staleTime: 5 * 60 * 1000,
      });
    }
  };

  // ── handleSelect (rail click / keyboard) ─────────────────────────────────
  const handleSelect = (id: string) => {
    if (id === sellerId) return;
    const oldIdx = allIds.indexOf(sellerId);
    const newIdx = allIds.indexOf(id);
    directionRef.current = newIdx >= oldIdx ? 1 : -1;
    setSellerId(id);
  };

  const direction = directionRef.current;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div
      className={[
        'min-h-screen bg-bg-0 text-ink-0',
        // Desktop: leave room for fixed left rail (tight — rail flush left)
        'xl:pl-[128px] xl:pr-9 xl:pt-7 xl:pb-12',
        // Tablet + mobile: no left padding (rail becomes horizontal strip)
        'md:px-4 md:pt-5 md:pb-12',
        // Mobile: 90px bottom to clear fixed BottomNav (RF-MOBILE-RESPONSIVE-04)
        'px-0 pt-0 pb-[90px] md:pb-12',
      ].join(' ')}
    >
      {/* Seller rail — outside AnimatePresence so it stays static */}
      <SellerRail
        preventistas={preventistas}
        activeId={sellerId}
        onSelect={handleSelect}
        onPrefetch={handlePrefetch}
      />

      {/* Content area (right of rail on xl) */}
      <div className="xl:max-w-[1240px]">
        <TopBar
          sellerName={currentSellerName}
          activeCategory={activeCategory}
          onCategoryChange={setActiveCategory}
          syncedAt={syncedAt}
        />

        {/* Main grid — layout depends on active tab */}
        {activeCategory === GENERICS_KEY ? (
          // ── GENERICOS layout: two large blocks side-by-side (stacked on mobile) ──
          <div className="grid xl:grid-cols-2 grid-cols-1 gap-5 items-start">
            {genericBlocksProps.map(({ key, props }) => (
              <AnimatePresence key={key} mode="wait" custom={direction}>
                <motion.div
                  key={sellerId + '-' + key}
                  custom={direction}
                  variants={slideVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                >
                  {isLoading || !props ? (
                    <HeroSkeleton />
                  ) : (
                    <GenericBlock {...props} />
                  )}
                </motion.div>
              </AnimatePresence>
            ))}
          </div>
        ) : (
          // ── CERVEZAS layout: hero left (420px) + brand grid right ──
          <div className="grid xl:grid-cols-[420px_1fr] grid-cols-1 gap-5 items-start">

            {/* ── Left: Hero ─────────────────────────────────────────────── */}
            <AnimatePresence mode="wait" custom={direction}>
              <motion.div
                key={sellerId + '-hero'}
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
              >
                {isLoading || !heroProps ? (
                  <HeroSkeleton />
                ) : (
                  <HeroCard {...heroProps} />
                )}
              </motion.div>
            </AnimatePresence>

            {/* ── Right: Brand detail ────────────────────────────────────── */}
            <AnimatePresence mode="wait" custom={direction}>
              <motion.div
                key={sellerId + '-right'}
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
              >
                {isLoading || brandCards.length === 0 ? (
                  <>
                    <div className="flex items-center justify-between mb-4">
                      <div className="h-4 w-48 bg-white/10 rounded animate-pulse" />
                    </div>
                    <BrandGridSkeleton />
                  </>
                ) : (
                  <>
                    <h2
                      className="font-sans font-semibold text-ink-1 mb-4"
                      style={{ fontSize: 13, letterSpacing: '0.02em' }}
                    >
                      Detalle por marca · {brandCards.length} marcas
                    </h2>
                    <BrandGrid cards={brandCards} />
                    <StatsStrip brands={brandStats} />
                  </>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        )}

        {/* Mobile: weather card below brand list */}
        <div className="md:hidden mt-4 mx-0">
          <WeatherWidget variant="mobile" city="salta" />
        </div>
      </div>

      {/* Mobile bottom nav */}
      <BottomNav
        activeKey="avance"
        onNavigate={(key) => {
          // Extend navigation here in Phase F
          void key;
        }}
      />
    </div>
  );
}
