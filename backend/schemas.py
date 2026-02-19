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
