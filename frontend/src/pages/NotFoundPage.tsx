import { Link } from 'react-router';

export default function NotFoundPage() {
  return (
    <div className="p-6 text-center">
      <h1 className="text-4xl font-bold text-brand-dark mt-8">404</h1>
      <p className="text-gray-400 mt-2 text-sm">Página no encontrada</p>
      <Link to="/" className="text-sm text-brand-dark font-medium hover:underline mt-4 inline-block">
        &larr; Volver al inicio
      </Link>
    </div>
  );
}
