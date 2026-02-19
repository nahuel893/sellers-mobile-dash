import { Link, useParams } from 'react-router';

export default function SucursalPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="p-6 text-center">
      <Link to="/" className="text-sm text-brand-dark font-medium hover:underline">
        &larr; Volver
      </Link>
      <h1 className="text-lg font-bold text-brand-dark mt-4">Sucursal {id}</h1>
      <p className="text-gray-400 mt-2 text-sm">Detalle sucursal — Fase 3</p>
    </div>
  );
}
