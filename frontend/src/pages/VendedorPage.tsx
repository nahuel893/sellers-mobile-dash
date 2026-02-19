import { useParams } from 'react-router';
import { fromSlug } from '../lib/format';
import { CATEGORIES, CATEGORY_NAMES, type CategoryKey } from '../lib/constants';
import { useVendedor } from '../hooks/use-vendedor';
import BackLink from '../components/BackLink';
import CategorySlide from '../components/CategorySlide';

export default function VendedorPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data, isLoading, error } = useVendedor(slug);

  const nombre = slug ? fromSlug(slug) : '';
  const pct = data?.categories.CERVEZAS?.resumen.pct_tendencia ?? 0;

  return (
    <>
      <BackLink to="/" />

      <div className="flex items-baseline gap-2 px-3 pb-2">
        <h1 className="text-lg font-extrabold text-brand-dark">{data?.nombre ?? nombre}</h1>
        {data && (
          <span className="text-xs text-gray-400 font-medium">{pct.toFixed(1)}%</span>
        )}
      </div>

      {isLoading && (
        <p className="text-center text-sm text-gray-400 py-8">Cargando datos...</p>
      )}

      {error && (
        <p className="text-center text-sm text-red-500 py-8">Error al cargar datos</p>
      )}

      {data && CATEGORIES.map((key) => {
        const catData = data.categories[key];
        if (!catData) return null;
        return (
          <div key={key} className="border-t border-gray-200 mt-2 mx-2">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider px-3 pt-3">
              {CATEGORY_NAMES[key as CategoryKey]}
            </h3>
            <CategorySlide categoryKey={key as CategoryKey} data={catData} />
          </div>
        );
      })}
    </>
  );
}
