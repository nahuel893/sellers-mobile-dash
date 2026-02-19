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

# --- Parámetros temporales (calculados dinámicamente) ---
from datetime import date

def _calcular_dias_habiles_mes():
    """Calcula días hábiles (L-V) del mes actual y transcurridos hasta hoy."""
    hoy = date.today()
    primer_dia = hoy.replace(day=1)
    # Último día del mes
    if hoy.month == 12:
        ultimo_dia = date(hoy.year + 1, 1, 1).replace(day=1)
    else:
        ultimo_dia = date(hoy.year, hoy.month + 1, 1)
    from datetime import timedelta
    ultimo_dia = ultimo_dia - timedelta(days=1)

    habiles_total = 0
    habiles_transcurridos = 0
    dia = primer_dia
    while dia <= ultimo_dia:
        if dia.weekday() < 5:  # Lunes=0 a Viernes=4
            habiles_total += 1
            if dia <= hoy:
                habiles_transcurridos += 1
        dia += timedelta(days=1)

    return habiles_total, habiles_transcurridos

DIAS_HABILES, DIAS_TRANSCURRIDOS = _calcular_dias_habiles_mes()
# Garantizar mínimo 1 para evitar division by zero en tendencia/vta_diaria
DIAS_TRANSCURRIDOS = max(DIAS_TRANSCURRIDOS, 1)
DIAS_RESTANTES = max(DIAS_HABILES - DIAS_TRANSCURRIDOS, 1)

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
