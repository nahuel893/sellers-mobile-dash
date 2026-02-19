import { useParams, useSearchParams } from 'react-router';
import { fromSlug } from '../lib/format';
import { useMapa } from '../hooks/use-mapa';
import BackLink from '../components/BackLink';
import CustomerMap from '../components/CustomerMap';

export default function MapaPage() {
  const { slug } = useParams<{ slug: string }>();
  const [searchParams] = useSearchParams();
  const sucursal = searchParams.get('sucursal');

  const nombre = slug ? fromSlug(slug) : '';
  const { data: clientes, isLoading, error } = useMapa(slug, sucursal);

  return (
    <>
      <BackLink to="/" />

      <div className="px-3 pb-3">
        <h1 className="text-lg font-extrabold text-brand-dark">
          Clientes de {nombre}
        </h1>
        {clientes && (
          <span className="text-xs text-gray-400 font-medium">
            {clientes.length} clientes
          </span>
        )}
      </div>

      {isLoading && (
        <p className="text-center text-sm text-gray-400 py-8">Cargando mapa...</p>
      )}

      {error && (
        <p className="text-center text-sm text-red-500 py-8">
          Error al cargar el mapa. Intente nuevamente.
        </p>
      )}

      {clientes && clientes.length === 0 && (
        <p className="text-center text-sm text-gray-400 py-8">
          Sin clientes con coordenadas para {nombre}
        </p>
      )}

      {clientes && clientes.length > 0 && (
        <div className="mx-2">
          <CustomerMap clientes={clientes} />
        </div>
      )}
    </>
  );
}
