import { useState } from 'react';
import { useParams, useSearchParams } from 'react-router';
import { fromSlug } from '../lib/format';
import { useSupervisor } from '../hooks/use-supervisor';
import BackLink from '../components/BackLink';
import CategoryToggle from '../components/CategoryToggle';
import SummaryBlock from '../components/SummaryBlock';
import VendorIndex from '../components/VendorIndex';
import VendorBlock from '../components/VendorBlock';

export default function SupervisorPage() {
  const { slug } = useParams<{ slug: string }>();
  const [searchParams] = useSearchParams();
  const sucursal = searchParams.get('sucursal');
  const [globalSlide, setGlobalSlide] = useState(0);

  const { data, isLoading, error } = useSupervisor(slug, sucursal);

  const nombre = slug ? fromSlug(slug) : '';
  const pct = data?.categories.CERVEZAS?.resumen.pct_tendencia ?? 0;
  const backTo = sucursal ? `/sucursal/${sucursal}` : '/';

  return (
    <>
      <BackLink to={backTo} />

      {isLoading && (
        <p className="text-center text-sm text-gray-400 py-8">Cargando datos...</p>
      )}

      {error && (
        <p className="text-center text-sm text-red-500 py-8">Error al cargar datos</p>
      )}

      {data && (
        <>
          <CategoryToggle activeIndex={globalSlide} onChange={setGlobalSlide} />

          <SummaryBlock
            title={data.nombre ?? nombre}
            pctTendencia={pct}
            categories={data.categories}
            variant="supervisor"
            globalSlideIndex={globalSlide}
          />

          <VendorIndex vendedores={data.vendedores} />

          {data.vendedores.map((v) => (
            <VendorBlock
              key={v.slug}
              vendedor={v}
              globalSlideIndex={globalSlide}
            />
          ))}
        </>
      )}
    </>
  );
}
