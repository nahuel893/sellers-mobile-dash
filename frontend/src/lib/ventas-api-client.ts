/**
 * Funciones de API para el módulo Ventas Mapa.
 * Mismo patrón que admin-api: token getter registrado desde AuthContext.
 */
import type {
  VentasFiltrosOpciones,
  VentasCliente,
  VentasHoverCliente,
  VentasClientesParams,
  VentasZona,
  VentasZonasParams,
  VentasCompro,
  VentasComproParams,
} from '../types/ventas';

const BASE_URL = import.meta.env.VITE_API_URL ?? '';

type TokenGetter = () => string | null;
let _getToken: TokenGetter = () => null;

export function setVentasTokenGetter(fn: TokenGetter): void {
  _getToken = fn;
}

// ---------------------------------------------------------------------------
// Fetch interno
// ---------------------------------------------------------------------------

type ParamValue = string | number | string[] | undefined | null;

async function ventasFetch<T>(
  path: string,
  params?: Record<string, ParamValue>,
): Promise<T> {
  const url = new URL(path, BASE_URL || window.location.origin);

  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v == null) continue;
      if (Array.isArray(v)) {
        v.forEach((item) => url.searchParams.append(k, item));
      } else {
        url.searchParams.set(k, String(v));
      }
    }
  }

  const token = _getToken();
  const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};

  const res = await fetch(url.toString(), {
    credentials: 'include',
    headers,
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// API pública
// ---------------------------------------------------------------------------

export const ventasApi = {
  getFiltrosOpciones: () =>
    ventasFetch<VentasFiltrosOpciones>('/api/ventas-filtros/opciones'),

  getClientesMapa: (params: VentasClientesParams) => {
    const q: Record<string, ParamValue> = {
      fecha_ini: params.fecha_ini,
      fecha_fin: params.fecha_fin,
      metrica: params.metrica,
    };
    if (params.fv) q.fv = params.fv;
    if (params.canal) q.canal = params.canal;
    if (params.subcanal) q.subcanal = params.subcanal;
    if (params.localidad) q.localidad = params.localidad;
    if (params.lista_precio != null) q.lista_precio = params.lista_precio;
    if (params.sucursal_id != null) q.sucursal_id = params.sucursal_id;
    if (params.ruta) q.ruta = params.ruta;
    if (params.preventista) q.preventista = params.preventista;
    if (params.genericos?.length) q.genericos = params.genericos;
    if (params.marcas?.length) q.marcas = params.marcas;
    return ventasFetch<VentasCliente[]>('/api/ventas-mapa/clientes', q);
  },

  getHoverCliente: (p: { id_cliente: number; fecha_ini: string; fecha_fin: string }) =>
    ventasFetch<VentasHoverCliente>(
      `/api/ventas-mapa/cliente/${p.id_cliente}/hover`,
      { fecha_ini: p.fecha_ini, fecha_fin: p.fecha_fin },
    ),

  getZonas: (params: VentasZonasParams) => {
    const q: Record<string, ParamValue> = {
      fecha_ini: params.fecha_ini,
      fecha_fin: params.fecha_fin,
      agrupacion: params.agrupacion,
    };
    if (params.fv) q.fv = params.fv;
    if (params.canal) q.canal = params.canal;
    if (params.subcanal) q.subcanal = params.subcanal;
    if (params.localidad) q.localidad = params.localidad;
    if (params.lista_precio != null) q.lista_precio = params.lista_precio;
    if (params.sucursal_id != null) q.sucursal_id = params.sucursal_id;
    if (params.ruta) q.ruta = params.ruta;
    if (params.preventista) q.preventista = params.preventista;
    if (params.genericos?.length) q.genericos = params.genericos;
    if (params.marcas?.length) q.marcas = params.marcas;
    return ventasFetch<VentasZona[]>('/api/ventas-mapa/zonas', q);
  },

  getCompro: (params: VentasComproParams) => {
    const q: Record<string, ParamValue> = {
      fecha_ini: params.fecha_ini,
      fecha_fin: params.fecha_fin,
    };
    if (params.fv) q.fv = params.fv;
    if (params.canal) q.canal = params.canal;
    if (params.subcanal) q.subcanal = params.subcanal;
    if (params.localidad) q.localidad = params.localidad;
    if (params.lista_precio != null) q.lista_precio = params.lista_precio;
    if (params.sucursal_id != null) q.sucursal_id = params.sucursal_id;
    if (params.ruta) q.ruta = params.ruta;
    if (params.preventista) q.preventista = params.preventista;
    return ventasFetch<VentasCompro[]>('/api/ventas-mapa/compro', q);
  },
};
