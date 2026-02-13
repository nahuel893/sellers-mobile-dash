# ============================================================
# Configuración del Dashboard de Preventa
# ============================================================

# --- Marcas que componen cada grupo ---
# TODO: Definir las marcas que componen estos grupos
MARCAS_MULTICERVEZAS = []   # Ej: ['ANDES', 'QUILMES', ...]
MARCAS_IMPORTADAS = []      # Ej: ['CORONA', 'BUDWEISER', ...]

# Grupos de marca en orden de visualización
GRUPOS_MARCA = ['SALTA', 'HEINEKEN', 'IMPERIAL', 'MILLER', 'MULTICERVEZAS', 'IMPORTADAS']

# Colores por grupo de marca
COLORES_GRUPO = {
    'SALTA':          '#1565C0',
    'HEINEKEN':       '#00A650',
    'IMPERIAL':       '#C8960C',
    'MILLER':         '#F9A825',
    'MULTICERVEZAS':  '#7B1FA2',
    'IMPORTADAS':     '#E65100',
}

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
