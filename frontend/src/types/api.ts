/** Matches backend/schemas.py — ResumenResponse */
export interface Resumen {
  pct_tendencia: number;
  ventas: number;
  cupo: number;
  falta: number;
  tendencia: number;
}

/** Matches DatosMarcaResponse */
export interface DatosMarca {
  grupo_marca: string | null;
  pct_tendencia: number;
  ventas: number;
  cupo: number;
  falta: number;
  tendencia: number;
}

/** Matches CategoryData */
export interface CategoryData {
  resumen: Resumen;
  datos: DatosMarca[];
}

/** Matches VendedorListItem */
export interface VendedorListItem {
  nombre: string;
  slug: string;
  categories: Record<string, CategoryData>;
}

/** Matches DashboardResponse */
export interface DashboardResponse {
  sucursal: Record<string, CategoryData>;
  supervisor: Record<string, CategoryData>;
  vendedores: VendedorListItem[];
}

/** Matches VendedorDetailResponse */
export interface VendedorDetailResponse {
  nombre: string;
  categories: Record<string, CategoryData>;
}

/** Matches SupervisorDetailResponse */
export interface SupervisorDetailResponse {
  nombre: string;
  categories: Record<string, CategoryData>;
  vendedores: VendedorListItem[];
}

/** Matches SucursalDetailResponse */
export interface SucursalDetailResponse {
  sucursal: string;
  categories: Record<string, CategoryData>;
  supervisores: string[];
}

/** Matches DiasHabilesResponse */
export interface DiasHabiles {
  habiles: number;
  transcurridos: number;
  restantes: number;
  fecha: string;
}

/** Matches CoberturaMarcaItem */
export interface CoberturaMarcaItem {
  marca: string;
  generico: string;
  cobertura: number;
  cupo: number;
  pct_cobertura: number;
}

/** Matches CoberturaVendedorData */
export interface CoberturaVendedorData {
  vendedor: string;
  sucursal: string;
  marcas: CoberturaMarcaItem[];
  total_cobertura: number;
  total_cupo: number;
  pct_total: number;
}

/** Matches CoberturaResponse */
export interface CoberturaResponse {
  sucursal: string;
  vendedores: CoberturaVendedorData[];
}

/** Matches ClienteResponse */
export interface Cliente {
  razon_social: string;
  fantasia: string | null;
  latitud: number;
  longitud: number;
  des_localidad: string | null;
}
