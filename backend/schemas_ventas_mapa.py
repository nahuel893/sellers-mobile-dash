"""Pydantic models para los endpoints ventas-mapa y ventas-filtros."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Filtros / opciones
# ---------------------------------------------------------------------------

class ListaPrecioOption(BaseModel):
    """Opción de lista de precio con código y descripción."""
    id_lista_precio: int
    des_lista_precio: Optional[str] = None


class SucursalOption(BaseModel):
    """Opción de sucursal con ID y descripción."""
    id_sucursal: int
    des_sucursal: str


class VentasFiltrosOpciones(BaseModel):
    """Opciones disponibles para cada dimensión de filtro."""
    canales: list[str]
    subcanales: list[str]
    localidades: list[str]
    listas_precio: list[ListaPrecioOption]
    sucursales: list[SucursalOption]
    rutas: list[str]           # formato "id_sucursal|id_ruta"
    preventistas: list[str]
    genericos: list[str]
    marcas: list[str]
    fecha_min: Optional[str] = None   # ISO date string
    fecha_max: Optional[str] = None   # ISO date string


# ---------------------------------------------------------------------------
# Clientes para el mapa
# ---------------------------------------------------------------------------

class VentasCliente(BaseModel):
    """Cliente con coordenadas y métrica agregada para el período."""
    id_cliente: int
    fantasia: Optional[str] = None
    razon_social: str
    latitud: float
    longitud: float
    canal: Optional[str] = None
    sucursal: Optional[str] = None
    ruta: Optional[str] = None          # formato "id_sucursal|id_ruta"
    preventista: Optional[str] = None
    bultos: float
    facturacion: float
    documentos: int


# ---------------------------------------------------------------------------
# Hover de cliente
# ---------------------------------------------------------------------------

class GenericoHover(BaseModel):
    """Métricas de un genérico en el hover del cliente."""
    generico: str
    m_act: float    # mes actual / período seleccionado
    m_ant: float    # mes anterior


class VentasHoverCliente(BaseModel):
    """Top genéricos + fijos para el tooltip de un cliente en el mapa."""
    id_cliente: int
    razon_social: str
    genericos: list[GenericoHover]


# ---------------------------------------------------------------------------
# Zonas (Fase 4 — Convex Hull)
# ---------------------------------------------------------------------------

class VentasZonaMetricas(BaseModel):
    """Métricas agregadas por zona."""
    bultos_m_act: float
    bultos_m_ant: float
    compradores_m_act: int     # clientes únicos con compras en el período
    compradores_m_ant: int
    por_generico: list[GenericoHover]   # reutilizamos GenericoHover (m_act/m_ant son bultos)


class VentasZona(BaseModel):
    """Zona geográfica representada por un polígono convex hull."""
    nombre: str                          # nombre de la ruta o preventista
    color_idx: int                       # índice en ZONE_COLORS (rota por mod)
    coords: list[list[float]]            # [[lon, lat], ...] — vértices del hull
    n_clientes: int                      # total de clientes en la zona (antes del outlier filter)
    metricas: VentasZonaMetricas


# ---------------------------------------------------------------------------
# Compro / No-compro (Fase 5)
# ---------------------------------------------------------------------------

class VentasCompro(BaseModel):
    """Cliente con indicador de compra en el período y última fecha de compra histórica."""
    id_cliente: int
    lat: float
    lon: float
    compro: bool
    ultima_compra: Optional[date] = None
