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
