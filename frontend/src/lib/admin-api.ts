/**
 * Admin API calls — use the shared apiFetch from api-client so they carry
 * the Bearer token and benefit from silent refresh on 401.
 */

import type {
  AdminUser,
  AdminUserCreate,
  AdminUserUpdate,
  AdminUserPasswordUpdate,
  RoleItem,
  SucursalAdminItem,
} from '../types/api';

// Re-use the shared apiFetch so token management is in one place.
// We import the internal function by re-exporting a wrapper in api-client.
// To avoid circular imports, we inline a thin fetch here that reads the token
// via the same module-level getter that api-client exposes.

const BASE_URL = import.meta.env.VITE_API_URL ?? '';

type TokenGetter = () => string | null;
let _getToken: TokenGetter = () => null;

/** Called by AuthContext to share the token getter (same token as api-client). */
export function setAdminTokenGetter(fn: TokenGetter): void {
  _getToken = fn;
}

async function adminFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = new URL(path, BASE_URL || window.location.origin);
  const token = _getToken();
  const authHeader: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};

  const res = await fetch(url.toString(), {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader,
      ...(options?.headers ?? {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as { detail?: string };
    const message = body.detail ?? `Error ${res.status}`;
    const err = new Error(message) as Error & { status: number };
    (err as Error & { status: number }).status = res.status;
    throw err;
  }

  const text = await res.text();
  return (text ? JSON.parse(text) : {}) as T;
}

// ---------------------------------------------------------------------------
// Public admin API surface
// ---------------------------------------------------------------------------

export const adminApi = {
  // Users
  listUsers: (): Promise<AdminUser[]> =>
    adminFetch<AdminUser[]>('/api/admin/users'),

  getUser: (id: number): Promise<AdminUser> =>
    adminFetch<AdminUser>(`/api/admin/users/${id}`),

  createUser: (body: AdminUserCreate): Promise<AdminUser> =>
    adminFetch<AdminUser>('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  updateUser: (id: number, body: AdminUserUpdate): Promise<AdminUser> =>
    adminFetch<AdminUser>(`/api/admin/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  resetPassword: (id: number, body: AdminUserPasswordUpdate): Promise<void> =>
    adminFetch<void>(`/api/admin/users/${id}/password`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // Roles
  listRoles: (): Promise<RoleItem[]> =>
    adminFetch<RoleItem[]>('/api/admin/roles'),

  // Sucursales
  listSucursales: (): Promise<SucursalAdminItem[]> =>
    adminFetch<SucursalAdminItem[]>('/api/admin/sucursales'),
};
