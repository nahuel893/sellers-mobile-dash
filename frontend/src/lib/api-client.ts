import type {
  DiasHabiles,
  DashboardResponse,
  VendedorDetailResponse,
  SupervisorDetailResponse,
  SucursalDetailResponse,
  Cliente,
  CoberturaResponse,
} from '../types/api';

const BASE_URL = import.meta.env.VITE_API_URL ?? '';

// ---------------------------------------------------------------------------
// Module-level token / auth callbacks (avoids circular imports with AuthContext)
// ---------------------------------------------------------------------------

type TokenGetter = () => string | null;
type TokenSetter = (token: string) => void;
type AuthFailureHandler = () => void;

let getAccessToken: TokenGetter = () => null;
let setAccessTokenFromRefresh: TokenSetter = () => {};
let onAuthFailure: AuthFailureHandler | null = null;

export function setAccessTokenGetter(fn: TokenGetter): void {
  getAccessToken = fn;
}

export function setAccessTokenSetter(fn: TokenSetter): void {
  setAccessTokenFromRefresh = fn;
}

export function setAuthFailureHandler(fn: AuthFailureHandler): void {
  onAuthFailure = fn;
}

// ---------------------------------------------------------------------------
// Single-refresh queue — prevents multiple simultaneous refresh calls
// ---------------------------------------------------------------------------

let isRefreshing = false;
let refreshQueue: Array<(token: string | null) => void> = [];

async function handleUnauthorized<T>(
  path: string,
  params: Record<string, string> | undefined,
  options: RequestInit | undefined,
): Promise<T> {
  if (isRefreshing) {
    // Queue this request until the ongoing refresh resolves
    return new Promise<T>((resolve, reject) => {
      refreshQueue.push((newToken) => {
        if (newToken) {
          resolve(apiFetch<T>(path, params, options));
        } else {
          reject(new Error('Session expired'));
        }
      });
    });
  }

  isRefreshing = true;
  try {
    const refreshRes = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });
    if (!refreshRes.ok) throw new Error('Refresh failed');
    const { access_token } = (await refreshRes.json()) as { access_token: string };

    // Push new token back into AuthContext state
    setAccessTokenFromRefresh(access_token);

    // Flush queued requests
    refreshQueue.forEach((cb) => cb(access_token));

    // Retry the original request
    return apiFetch<T>(path, params, options);
  } catch {
    refreshQueue.forEach((cb) => cb(null));
    onAuthFailure?.();
    throw new Error('Session expired');
  } finally {
    isRefreshing = false;
    refreshQueue = [];
  }
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

async function apiFetch<T>(
  path: string,
  params?: Record<string, string>,
  options?: RequestInit,
): Promise<T> {
  const url = new URL(path, BASE_URL || window.location.origin);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v != null) url.searchParams.set(k, v);
    }
  }

  const token = getAccessToken();
  const authHeader: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};

  const res = await fetch(url.toString(), {
    ...options,
    credentials: 'include',
    headers: {
      ...authHeader,
      ...(options?.headers ?? {}),
    },
  });

  // 401 on a non-auth endpoint → attempt silent refresh
  if (res.status === 401 && !path.includes('/api/auth/')) {
    return handleUnauthorized<T>(path, params, options);
  }

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Public API surface
// ---------------------------------------------------------------------------

export const api = {
  getDiasHabiles: () => apiFetch<DiasHabiles>('/api/config/dias-habiles'),
  getSucursales: () => apiFetch<string[]>('/api/sucursales'),
  getSupervisores: (sucursal: string) =>
    apiFetch<string[]>('/api/supervisores', { sucursal }),
  getVendedores: (supervisor: string, sucursal: string) =>
    apiFetch<string[]>('/api/vendedores', { supervisor, sucursal }),
  getDashboard: (supervisor: string, sucursal: string) =>
    apiFetch<DashboardResponse>('/api/dashboard', { supervisor, sucursal }),
  getVendedor: (slug: string) =>
    apiFetch<VendedorDetailResponse>(`/api/vendedor/${slug}`),
  getSupervisor: (slug: string, sucursal?: string) =>
    apiFetch<SupervisorDetailResponse>(
      `/api/supervisor/${slug}`,
      sucursal ? { sucursal } : undefined,
    ),
  getSucursal: (id: string) =>
    apiFetch<SucursalDetailResponse>(`/api/sucursal/${id}`),
  getMapa: (slug: string, sucursal?: string) =>
    apiFetch<Cliente[]>(
      `/api/mapa/${slug}`,
      sucursal ? { sucursal } : undefined,
    ),
  getCobertura: (sucursal?: string, supervisor?: string, vendedor?: string) => {
    const params: Record<string, string> = {};
    if (sucursal) params.sucursal = sucursal;
    if (supervisor) params.supervisor = supervisor;
    if (vendedor) params.vendedor = vendedor;
    return apiFetch<CoberturaResponse>(
      '/api/cobertura',
      Object.keys(params).length ? params : undefined,
    );
  },
};
