/**
 * Tipos TypeScript para el módulo Ventas Mapa.
 * Deben mantenerse 1:1 con backend/schemas_ventas_mapa.py
 */

// ---------------------------------------------------------------------------
// Opciones de filtros
// ---------------------------------------------------------------------------

export interface ListaPrecioOption {
  id_lista_precio: number;
  des_lista_precio: string | null;
}

export interface SucursalOption {
  id_sucursal: number;
  des_sucursal: string;
}

export interface VentasFiltrosOpciones {
  canales: string[];
  subcanales: string[];
  localidades: string[];
  listas_precio: ListaPrecioOption[];
  sucursales: SucursalOption[];
  rutas: string[];         // formato "id_sucursal|id_ruta"
  preventistas: string[];
  genericos: string[];
  marcas: string[];
  fecha_min: string | null;
  fecha_max: string | null;
}

// ---------------------------------------------------------------------------
// Cliente para el mapa
// ---------------------------------------------------------------------------

export interface VentasCliente {
  id_cliente: number;
  fantasia: string | null;
  razon_social: string;
  latitud: number;
  longitud: number;
  canal: string | null;
  sucursal: string | null;
  ruta: string | null;        // formato "id_sucursal|id_ruta"
  preventista: string | null;
  bultos: number;
  facturacion: number;
  documentos: number;
}

// ---------------------------------------------------------------------------
// Hover de cliente
// ---------------------------------------------------------------------------

export interface GenericoHover {
  generico: string;
  m_act: number;
  m_ant: number;
}

export interface VentasHoverCliente {
  id_cliente: number;
  razon_social: string;
  genericos: GenericoHover[];
}

// ---------------------------------------------------------------------------
// Estado de filtros (UI state)
// ---------------------------------------------------------------------------

export type VentasMetrica = 'bultos' | 'facturacion' | 'documentos';
export type VentasFV = '1' | '4' | 'AMBAS';
export type VentasTipoSucursal = 'TODAS' | 'SUCURSALES' | 'CASA_CENTRAL';

/** Modo de visualización del mapa */
export type VentasMapaModo = 'burbujas' | 'calor' | 'compro';

/** Sub-modo dentro del modo calor */
export type CalorSubmodo = 'difuso' | 'grilla';

export interface VentasFiltrosState {
  fecha_ini: string;
  fecha_fin: string;
  canal: string[];
  subcanal: string[];
  localidad: string[];
  lista_precio: number[];
  tipo_sucursal: VentasTipoSucursal;
  sucursal_ids: number[];
  genericos: string[];
  marcas: string[];
  fv: VentasFV;
  rutas: string[];
  preventistas: string[];
  metrica: VentasMetrica;
  zonas_agrupacion: VentasZonasAgrupacion;
}

// ---------------------------------------------------------------------------
// Zonas (Fase 4 — Convex Hull)
// ---------------------------------------------------------------------------

export interface GenericoZona {
  generico: string;
  m_act: number;
  m_ant: number;
}

export interface VentasZonaMetricas {
  bultos_m_act: number;
  bultos_m_ant: number;
  compradores_m_act: number;
  compradores_m_ant: number;
  por_generico: GenericoZona[];
}

export interface VentasZona {
  nombre: string;
  color_idx: number;
  coords: [number, number][];   // [[lon, lat], ...] — orden deck.gl
  n_clientes: number;
  metricas: VentasZonaMetricas;
}

export type VentasZonasAgrupacion = 'OCULTAS' | 'ruta' | 'preventista';

export interface VentasZonasParams extends VentasClientesParams {
  agrupacion: 'ruta' | 'preventista';
}

// ---------------------------------------------------------------------------
// Parámetros para el endpoint /api/ventas-mapa/clientes
// ---------------------------------------------------------------------------

export interface VentasClientesParams {
  fecha_ini: string;
  fecha_fin: string;
  fv?: string;
  canal?: string;
  subcanal?: string;
  localidad?: string;
  lista_precio?: number;
  sucursal_id?: number;
  ruta?: string;
  preventista?: string;
  genericos?: string[];
  marcas?: string[];
  metrica: VentasMetrica;
}

// ---------------------------------------------------------------------------
// Compro / No-compro (Fase 5)
// ---------------------------------------------------------------------------

export interface VentasCompro {
  id_cliente: number;
  lat: number;
  lon: number;
  compro: boolean;
  ultima_compra: string | null;  // ISO date string o null
}

// ---------------------------------------------------------------------------
// Búsqueda de cliente (Fase 6)
// ---------------------------------------------------------------------------

export interface VentasClienteBusqueda {
  id_cliente: number;
  razon_social: string;
  fantasia: string | null;
  localidad: string | null;
  sucursal: string | null;
  latitud: number | null;
  longitud: number | null;
}

/** Parámetros para /api/ventas-mapa/compro (mismo pipeline de filtros que clientes, sin metrica) */
export interface VentasComproParams {
  fecha_ini: string;
  fecha_fin: string;
  fv?: string;
  canal?: string;
  subcanal?: string;
  localidad?: string;
  lista_precio?: number;
  sucursal_id?: number;
  ruta?: string;
  preventista?: string;
}
