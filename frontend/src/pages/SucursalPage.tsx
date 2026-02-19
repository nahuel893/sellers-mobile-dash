import { useState } from 'react';
import { Link, useParams } from 'react-router';
import { useQueries } from '@tanstack/react-query';
import { useSucursal } from '../hooks/use-sucursal';
import { api } from '../lib/api-client';
import { toSlug } from '../lib/format';
import BackLink from '../components/BackLink';
import CategoryToggle from '../components/CategoryToggle';
import SummaryBlock from '../components/SummaryBlock';
import CategoryCarousel from '../components/CategoryCarousel';

export default function SucursalPage() {
  const { id } = useParams<{ id: string }>();
  const [globalSlide, setGlobalSlide] = useState(0);

  const { data: sucursalData, isLoading, error } = useSucursal(id);

  const supervisorQueries = useQueries({
    queries: (sucursalData?.supervisores ?? []).map((nombre) => ({
      queryKey: ['supervisor', nombre, id],
      queryFn: () => api.getSupervisor(toSlug(nombre), id),
    })),
  });

  const sucursalPct = sucursalData?.categories.CERVEZAS?.resumen.pct_tendencia ?? 0;

  return (
    <>
      <BackLink to="/" />

      {isLoading && (
        <p className="text-center text-sm text-gray-400 py-8">Cargando datos...</p>
      )}

      {error && (
        <p className="text-center text-sm text-red-500 py-8">Error al cargar datos</p>
      )}

      {sucursalData && (
        <>
          <CategoryToggle activeIndex={globalSlide} onChange={setGlobalSlide} />

          <SummaryBlock
            title={sucursalData.sucursal}
            pctTendencia={sucursalPct}
            categories={sucursalData.categories}
            variant="sucursal"
            globalSlideIndex={globalSlide}
          />

          {sucursalData.supervisores.map((nombre, i) => {
            const query = supervisorQueries[i];
            const supPct = query?.data?.categories.CERVEZAS?.resumen.pct_tendencia ?? 0;
            const slug = toSlug(nombre);

            return (
              <div
                key={nombre}
                className="border-t-2 border-gray-300 bg-gradient-to-b from-gray-50 to-white rounded-lg mt-3 mx-2 overflow-hidden"
              >
                <div className="flex items-baseline gap-2 px-3 pt-3">
                  <Link
                    to={`/supervisor/${slug}?sucursal=${id}`}
                    className="text-sm font-bold text-brand-dark hover:underline no-underline"
                  >
                    {nombre}
                  </Link>
                  {query?.data && (
                    <span className="text-xs text-gray-400 font-medium">
                      {supPct.toFixed(1)}%
                    </span>
                  )}
                </div>
                {query?.isLoading && (
                  <p className="text-xs text-gray-400 px-3 py-4">Cargando...</p>
                )}
                {query?.data && (
                  <CategoryCarousel
                    categories={query.data.categories}
                    globalSlideIndex={globalSlide}
                  />
                )}
              </div>
            );
          })}
        </>
      )}
    </>
  );
}
