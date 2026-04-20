import { useState, useEffect, type FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router';
import { useAuth } from '../hooks/use-auth';

export default function LoginPage() {
  const { login, user, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Path to redirect after successful login
  const from =
    (location.state as { from?: { pathname?: string; search?: string } } | null)?.from?.pathname ?? '/';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Already authenticated → redirect away from /login
  useEffect(() => {
    if (!authLoading && user) {
      navigate(from, { replace: true });
    }
  }, [user, authLoading, from, navigate]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;

    setSubmitting(true);
    setError(null);
    try {
      await login({ username, password });
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al iniciar sesión');
    } finally {
      setSubmitting(false);
    }
  };

  // While restoring session (page reload) don't flash the form
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#f0f2f5]">
        <div className="text-sm text-gray-400">Cargando…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f0f2f5] flex flex-col">
      {/* Brand header — matches app gradient */}
      <header className="bg-gradient-to-br from-brand-dark to-brand-dark2 text-white px-4 pt-5 pb-6 rounded-b-[20px]">
        <h1 className="text-lg font-extrabold tracking-tight">Avance Preventa</h1>
        <p className="text-xs text-white/60 mt-0.5">Iniciá sesión para continuar</p>
      </header>

      {/* Login form */}
      <main className="flex-1 flex items-start justify-center px-4 pt-10">
        <form
          onSubmit={handleSubmit}
          className="w-full max-w-sm bg-white rounded-[16px] shadow-sm p-6 flex flex-col gap-4"
          noValidate
        >
          <h2 className="text-base font-bold text-gray-800">Iniciar sesión</h2>

          {/* Error message */}
          {error && (
            <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          {/* Username */}
          <div className="flex flex-col gap-1">
            <label htmlFor="username" className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              Usuario
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              autoCapitalize="none"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={submitting}
              className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-dark/30 disabled:opacity-50"
              placeholder="nombre.apellido"
            />
          </div>

          {/* Password */}
          <div className="flex flex-col gap-1">
            <label htmlFor="password" className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
              className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-dark/30 disabled:opacity-50"
              placeholder="••••••••"
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting || !username || !password}
            className="mt-1 bg-brand-dark text-white text-sm font-semibold py-2.5 rounded-lg disabled:opacity-50 hover:bg-brand-dark2 transition-colors"
          >
            {submitting ? 'Ingresando…' : 'Ingresar'}
          </button>
        </form>
      </main>
    </div>
  );
}
