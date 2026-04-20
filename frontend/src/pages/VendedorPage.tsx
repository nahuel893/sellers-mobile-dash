import { useParams } from 'react-router';
import { fromSlug, colorByPerformance } from '../lib/format';
import { CATEGORIES, CATEGORY_NAMES, type CategoryKey } from '../lib/constants';
import { useVendedor } from '../hooks/use-vendedor';
import { useCobertura } from '../hooks/use-cobertura';
import BackLink from '../components/BackLink';
import CategorySlide from '../components/CategorySlide';

export default function VendedorPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data, isLoading, error } = useVendedor(slug);
  const nombre = slug ? fromSlug(slug) : '';
  const { data: cobertura } = useCobertura(undefined, undefined, data?.nombre ?? nombre);

  const pct = data?.categories.CERVEZAS?.resumen.pct_tendencia ?? 0;
  const cobVendedor = cobertura?.vendedores?.[0];
  const marcas = cobVendedor ? [...cobVendedor.marcas].sort((a, b) => b.cupo - a.cupo) : [];

  return (
    <>
      <BackLink to="/sellers" />

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

      {marcas.length > 0 && (
        <div className="border-t border-gray-200 mt-2 mx-2">
          <h3 className="text-sm font-bold text-brand-dark uppercase tracking-wider px-3 pt-3 pb-2">
            Cobertura
          </h3>
          <div className="bg-white rounded-xl shadow-sm px-2 py-2 mx-2 mb-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[10px] uppercase text-gray-500 tracking-wider">
                  <th className="text-left py-1 px-1 font-medium">Marca</th>
                  <th className="text-right py-1 px-1 font-medium">Real</th>
                  <th className="text-right py-1 px-1 font-medium">Cupo</th>
                  <th className="text-right py-1 px-1 font-medium">Falta</th>
                  <th className="text-right py-1 px-1 font-medium">%</th>
                </tr>
              </thead>
              <tbody>
                {marcas.map((m, i) => {
                  const falta = Math.max(m.cupo - m.cobertura, 0);
                  const color = colorByPerformance(m.pct_cobertura);
                  const prevGenerico = i > 0 ? marcas[i - 1].generico : null;
                  const showHeader = m.generico !== prevGenerico;
                  return (
                    <>
                      {showHeader && (
                        <tr key={`hdr-${m.generico}`} className="bg-gray-50">
                          <td colSpan={5} className="py-1.5 px-1 text-[10px] font-bold uppercase tracking-wider text-gray-500">
                            {m.generico}
                          </td>
                        </tr>
                      )}
                      <tr key={m.marca} className="border-t border-gray-50">
                        <td className="py-1.5 px-1 pl-3 font-semibold text-brand-dark text-xs">{m.marca}</td>
                        <td className="py-1.5 px-1 text-right font-bold" style={{ color }}>{m.cobertura}</td>
                        <td className="py-1.5 px-1 text-right font-bold text-brand-dark">{m.cupo}</td>
                        <td className="py-1.5 px-1 text-right font-bold text-red-500">{falta > 0 ? `-${falta}` : '—'}</td>
                        <td className="py-1.5 px-1 text-right font-bold" style={{ color }}>{m.pct_cobertura.toFixed(0)}%</td>
                      </tr>
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
