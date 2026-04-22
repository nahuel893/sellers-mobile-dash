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

// --- Auth types ---

export type Role = 'admin' | 'gerente' | 'supervisor' | 'vendedor';

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  role: Role;
  nombre_completo: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  user: AuthUser;
}

export interface TokenRefreshResponse {
  access_token: string;
  token_type: 'bearer';
}

// --- Admin types ---

/** Matches auth/admin_models.py UserListItem */
export interface AdminUser {
  id: number;
  username: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  sucursales: number[];
}

/** Matches auth/admin_models.py UserCreate */
export interface AdminUserCreate {
  username: string;
  password: string;
  full_name: string;
  role: Role;
  sucursales?: number[];
}

/** Matches auth/admin_models.py UserUpdate — all optional */
export interface AdminUserUpdate {
  full_name?: string;
  role?: Role;
  is_active?: boolean;
  sucursales?: number[];
}

/** Matches auth/admin_models.py UserPasswordUpdate */
export interface AdminUserPasswordUpdate {
  password: string;
}

/** Matches auth/admin_models.py RoleItem */
export interface RoleItem {
  id: number;
  name: string;
}

/** Matches auth/admin_models.py SucursalItem */
export interface SucursalAdminItem {
  id: number;
  descripcion: string;
}

// --- Dashboard redesign types (Phase B schemas) ---

/** Matches PreventistaItem */
export interface Preventista {
  nombre: string;
  slug: string;
  iniciales: string;
  ruta: string | null;
}

/** Matches SparklineDia */
export interface SparklineDia {
  fecha: string;
  por_grupo: Record<string, number>;
}

/** Matches SparklineResponse */
export interface SparklineResponse {
  vendedor: string;
  dias: number;
  puntos: SparklineDia[];
}

/** Matches BrandDelta */
export interface BrandDelta {
  grupo_marca: string;
  pct_actual: number;
  pct_anterior: number | null;
  delta_pp: number | null;
}

/** Matches DeltaResponse */
export interface DeltaResponse {
  vendedor: string;
  deltas: BrandDelta[];
}

/** Matches WeatherResponse */
export interface WeatherResponse {
  city: string;
  temp_c: number;
  feels_like_c: number;
  min_c: number;
  max_c: number;
  humidity_pct: number;
  wind_kmh: number;
  condition: string;
  icon: string;
  observed_at: string;
}
