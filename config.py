# ============================================================
# Configuración del Dashboard de Preventa
# ============================================================

# --- Marcas que componen cada grupo (dim_articulo.marca → grupo_marca) ---
MARCAS_MULTICERVEZAS = ['SCHNEIDER', 'AMSTEL', 'WARSTEINER', 'GROLSCH', 'BIECKERT', 'ISENBECK', 'IGUANA']
MARCAS_IMPORTADAS = ['SOL', 'BLUE MOON', 'KUNSTMAN', 'KUNSTMANN']

# Grupos de marca en orden de visualización
GRUPOS_MARCA = ['SALTA', 'HEINEKEN', 'IMPERIAL', 'MILLER', 'MULTICERVEZAS', 'IMPORTADAS']

# Mapeo completo: dim_articulo.marca → grupo_marca del dashboard
MAPEO_MARCA_GRUPO = {
    'SALTA':          'SALTA',
    'NORTE':          'SALTA',       # TODO: revisar si NORTE siempre suma a SALTA (confirmado solo para Güemes)
    'SALTA CAUTIVA1': 'SALTA CAUTIVA1',  # Independiente: no tiene gauge propio pero suma al total cervezas
    'HEINEKEN':       'HEINEKEN',
    'IMPERIAL':       'IMPERIAL',
    'MILLER':         'MILLER',
    'SCHNEIDER':      'MULTICERVEZAS',
    'AMSTEL':         'MULTICERVEZAS',
    'WARSTEINER':     'MULTICERVEZAS',
    'GROLSCH':        'MULTICERVEZAS',
    'BIECKERT':       'MULTICERVEZAS',
    'ISENBECK':       'MULTICERVEZAS',
    'IGUANA':         'MULTICERVEZAS',
    'SOL':            'IMPORTADAS',
    'BLUE MOON':      'IMPORTADAS',
    'KUNSTMAN':       'IMPORTADAS',
    'KUNSTMANN':      'IMPORTADAS',
}

# Mapeo de DESAGREGADO (Excel cupos) → (categoria, grupo_marca)
# NOTA: 'CERVEZAS' es el total de la categoría (no sumar los individuales).
# 'SALTA CAUTIVA1' se excluye: su cupo individual no se trackea, pero su venta
# sí suma al total cervezas (ya incluida en el total CERVEZAS del Excel).
MAPEO_DESAGREGADO_CUPO = {
    'CERVEZAS':       ('CERVEZAS', 'TOTAL_CERVEZAS'),  # Total cervezas (usar este, no sumar individuales)
    'SALTA':          ('CERVEZAS', 'SALTA'),
    'HEINEKEN':       ('CERVEZAS', 'HEINEKEN'),
    'IMPERIAL':       ('CERVEZAS', 'IMPERIAL'),
    'MILLER':         ('CERVEZAS', 'MILLER'),
    'MULTICERVEZAS':  ('CERVEZAS', 'MULTICERVEZAS'),
    'IMPORTADAS':     ('CERVEZAS', 'IMPORTADAS'),
    'AGUAS DANONE':   ('AGUAS_DANONE', None),
    'MULTICCU':       ('MULTICCU', None),
}

# Colores por grupo de marca
COLORES_GRUPO = {
    'SALTA':          '#1565C0',
    'HEINEKEN':       '#00A650',
    'IMPERIAL':       '#C8960C',
    'MILLER':         '#F9A825',
    'MULTICERVEZAS':  '#7B1FA2',
    'IMPORTADAS':     '#E65100',
}

# --- Categorías de producto (slides del carrusel) ---
CATEGORIAS = ['CERVEZAS', 'MULTICCU', 'AGUAS_DANONE']

NOMBRES_CATEGORIA = {
    'CERVEZAS':     'Cervezas',
    'MULTICCU':     'MultiCCU',
    'AGUAS_DANONE': 'Aguas Danone',
}

# Mapeo de genérico (dim_articulo.generico) → categoría del dashboard
MAPEO_GENERICO_CATEGORIA = {
    'CERVEZAS':          'CERVEZAS',
    'AGUAS DANONE':      'AGUAS_DANONE',
    'VINOS CCU':         'MULTICCU',
    'SIDRAS Y LICORES':  'MULTICCU',
}

# --- Normalización de nombres de vendedor ---
# Nombre en cupos Excel (descripcion) puede diferir de dim_cliente/dim_vendedor.
# Clave: nombre en cupos Excel → nombre en BD (dim_vendedor.des_vendedor)
NORMALIZAR_VENDEDOR = {
    'SUB DISTRIBUIDORES': 'SUB DISTRIBUIDOR',
}

# Vendedores a excluir (aparecen en dim_cliente pero no son preventistas)
VENDEDORES_EXCLUIR = []

# --- Parámetros temporales (se calcularán dinámicamente después) ---
DIAS_HABILES = 24
DIAS_TRANSCURRIDOS = 11
DIAS_RESTANTES = 13

# --- Colores de performance ---
COLOR_VERDE = '#4CAF50'
COLOR_AMARILLO = '#FFC107'
COLOR_ROJO = '#F44336'

def color_por_rendimiento(pct_tendencia):
    """Retorna color según % de tendencia vs cupo."""
    if pct_tendencia >= 80:
        return COLOR_VERDE
    elif pct_tendencia >= 70:
        return COLOR_AMARILLO
    else:
        return COLOR_ROJO
