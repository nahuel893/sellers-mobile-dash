import { type ReactNode } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router';
import { useAuth } from '../hooks/use-auth';

interface ProtectedRouteProps {
  children?: ReactNode;
}

/**
 * Wraps routes that require authentication.
 *
 * - While the initial session restore is in flight (isLoading), renders a
 *   spinner to avoid a flash-redirect.
 * - When unauthenticated, redirects to /login, saving the intended path in
 *   location state so LoginPage can navigate back after login.
 * - When authenticated, renders children or <Outlet /> (for layout routes).
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#f0f2f5]">
        <div className="text-sm text-gray-400">Cargando…</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
}
