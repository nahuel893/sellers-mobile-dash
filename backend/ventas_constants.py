"""
Constantes para el módulo ventas-mapa.

Separado de config.py para evitar contaminar las constantes del dashboard clásico.
"""

# Genéricos a excluir del mapa y filtros (sin valor comercial relevante para la vista mapa)
GENERICOS_EXCLUIDOS: list[str] = [
    'ENVACES CCU',
    'AGUAS Y SODAS',
    'APERITIVOS',
    'DISPENSER',
    'ENVASES PALAU',
    'GASEOSA',
    'MARKETING BRANCA',
    'MARKETING',
]

# Genéricos que siempre aparecen en el hover del cliente, aunque tengan ventas = 0
GENERICOS_HOVER_FIJOS: list[str] = [
    'CERVEZAS',
    'AGUAS DANONE',
    'SIDRAS Y LICORES',
    'VINOS CCU',
    'FRATELLI B',
    'VINOS',
    'VINOS FINOS',
]

# Fuerza de ventas
FV_PREVENTA = '1'    # FV1 — preventa
FV_AUTOVENTA = '4'   # FV4 — autoventa
FV_AMBAS = 'AMBAS'

# Métricas disponibles para el mapa
METRICA_BULTOS = 'bultos'
METRICA_FACTURACION = 'facturacion'
METRICA_DOCUMENTOS = 'documentos'
METRICAS_VALIDAS = {METRICA_BULTOS, METRICA_FACTURACION, METRICA_DOCUMENTOS}

# Roles con acceso irrestricto (ven todas las sucursales)
ROLES_SIN_FILTRO_SUCURSAL: set[str] = {'admin', 'gerente'}
