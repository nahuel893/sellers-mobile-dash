import type {
  DiasHabiles,
  DashboardResponse,
  VendedorDetailResponse,
  SupervisorDetailResponse,
  SucursalDetailResponse,
  Cliente,
} from '../types/api';

const BASE_URL = import.meta.env.VITE_API_URL ?? '';

async function apiFetch<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(path, BASE_URL || window.location.origin);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v != null) url.searchParams.set(k, v);
    }
  }
  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

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
};
