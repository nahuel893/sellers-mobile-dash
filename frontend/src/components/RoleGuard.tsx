import { type ReactNode } from 'react';
import { Navigate } from 'react-router';
import type { Role } from '../types/api';
import { useAuth } from '../hooks/use-auth';

interface RoleGuardProps {
  /** Roles allowed to access the wrapped content. */
  roles: Role[];
  /** Where to redirect if the user's role is not allowed. Defaults to '/'. */
  redirectTo?: string;
  children: ReactNode;
}

/**
 * Composable role-based guard. Must be rendered inside a ProtectedRoute
 * (i.e., after authentication is confirmed) — never before.
 *
 * Redirects to `redirectTo` when:
 * - user is null (defensive, should not happen inside ProtectedRoute)
 * - user.role is not in the allowed list
 */
export function RoleGuard({ roles, redirectTo = '/', children }: RoleGuardProps) {
  const { user } = useAuth();

  if (!user || !roles.includes(user.role)) {
    return <Navigate to={redirectTo} replace />;
  }

  return <>{children}</>;
}
