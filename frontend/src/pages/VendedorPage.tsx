import { Link, useParams } from 'react-router';
import { fromSlug } from '../lib/format';

export default function VendedorPage() {
  const { slug } = useParams<{ slug: string }>();
  const nombre = slug ? fromSlug(slug) : '';

  return (
    <div className="p-6 text-center">
      <Link to="/" className="text-sm text-brand-dark font-medium hover:underline">
        &larr; Volver
      </Link>
      <h1 className="text-lg font-bold text-brand-dark mt-4">{nombre}</h1>
      <p className="text-gray-400 mt-2 text-sm">Detalle vendedor — Fase 3</p>
    </div>
  );
}
