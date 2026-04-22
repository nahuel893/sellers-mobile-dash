"""Pydantic models para las respuestas de la API."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ResumenResponse(BaseModel):
    """Métricas resumen para un vendedor/supervisor/sucursal en una categoría."""
    pct_tendencia: float
    ventas: int
    cupo: int
    falta: int
    tendencia: int


class DatosMarcaResponse(BaseModel):
    """Fila de desglose por grupo de marca."""
    grupo_marca: Optional[str] = None
    pct_tendencia: float
    ventas: int
    cupo: int
    falta: int
    tendencia: float


class CategoryData(BaseModel):
    """Resumen + datos para una categoría."""
    resumen: ResumenResponse
    datos: list[DatosMarcaResponse]


class VendedorListItem(BaseModel):
    """Vendedor en listado (vista dashboard)."""
    nombre: str
    slug: str
    categories: dict[str, CategoryData]


class VendedorDetailResponse(BaseModel):
    """Detalle completo de vendedor."""
    nombre: str
    categories: dict[str, CategoryData]


class SupervisorDetailResponse(BaseModel):
    """Detalle completo de supervisor."""
    nombre: str
    categories: dict[str, CategoryData]
    vendedores: list[VendedorListItem]


class SucursalDetailResponse(BaseModel):
    """Detalle completo de sucursal."""
    sucursal: str
    categories: dict[str, CategoryData]
    supervisores: list[str]


class DashboardResponse(BaseModel):
    """Datos completos del dashboard (vista home)."""
    sucursal: dict[str, CategoryData]
    supervisor: dict[str, CategoryData]
    vendedores: list[VendedorListItem]


class ClienteResponse(BaseModel):
    """Cliente con coordenadas para el mapa."""
    razon_social: str
    fantasia: Optional[str] = None
    latitud: float
    longitud: float
    des_localidad: Optional[str] = None


class DiasHabilesResponse(BaseModel):
    """Info de días hábiles del mes."""
    habiles: int
    transcurridos: int
    restantes: int
    fecha: str


# --- Cobertura ---

# --- Dashboard redesign schemas ---

class PreventistaItem(BaseModel):
    """Preventista para la barra lateral del dashboard."""
    nombre: str
    slug: str
    iniciales: str
    ruta: str | None = None


class SparklineDia(BaseModel):
    """Punto de ventas de un día en el sparkline."""
    fecha: str  # ISO date string
    por_grupo: dict[str, int]


class SparklineResponse(BaseModel):
    """Respuesta del endpoint de sparkline."""
    vendedor: str
    dias: int
    puntos: list[SparklineDia]


class BrandDelta(BaseModel):
    """Delta de porcentaje para un grupo de marca (actual vs mes anterior)."""
    grupo_marca: str
    pct_actual: float
    pct_anterior: float | None
    delta_pp: float | None


class DeltaResponse(BaseModel):
    """Respuesta del endpoint de delta pp."""
    vendedor: str
    deltas: list[BrandDelta]


class WeatherResponse(BaseModel):
    """Respuesta del endpoint de clima."""
    city: str
    temp_c: int
    feels_like_c: int
    min_c: int
    max_c: int
    humidity_pct: int
    wind_kmh: int
    condition: str
    icon: str
    observed_at: str  # ISO datetime


class CoberturaMarcaItem(BaseModel):
    """Cobertura de una marca para un vendedor."""
    marca: str
    generico: str
    cobertura: int
    cupo: int
    pct_cobertura: float


class CoberturaVendedorResponse(BaseModel):
    """Cobertura de un vendedor con desglose por marca."""
    vendedor: str
    sucursal: str
    marcas: list[CoberturaMarcaItem]
    total_cobertura: int
    total_cupo: int
    pct_total: float


class CoberturaResponse(BaseModel):
    """Cobertura de una sucursal con desglose por vendedor."""
    sucursal: str
    vendedores: list[CoberturaVendedorResponse]
