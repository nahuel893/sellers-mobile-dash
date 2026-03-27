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
# Kept empty for potential future use. Previously mapped cupos Excel names to
# dim_vendedor.des_vendedor. No longer needed since both ventas query and cupos
# now use dim_cliente.des_personal_fv1 as the single vendor identifier.
NORMALIZAR_VENDEDOR = {}

# Vendedores a excluir (aparecen en dim_cliente pero no son preventistas)
VENDEDORES_EXCLUIR = []

# --- Parámetros temporales (calculados dinámicamente) ---
import logging
from datetime import date, timedelta

import json
from pathlib import Path

import holidays as _holidays_lib

logger = logging.getLogger(__name__)

_FERIADOS_IGNORAR_PATH = Path(__file__).parent / "feriados_ignorar.json"

def _cargar_feriados_ignorar() -> set[date]:
    """Carga fechas que la empresa NO toma como feriado desde el JSON."""
    if not _FERIADOS_IGNORAR_PATH.exists():
        return set()
    try:
        data = json.loads(_FERIADOS_IGNORAR_PATH.read_text(encoding="utf-8"))
        fechas = set()
        for entry in data.get("ignorar", []):
            f = date.fromisoformat(entry["fecha"])
            fechas.add(f)
            logger.info("Feriado IGNORADO (empresa trabaja): %s — %s", entry["fecha"], entry.get("motivo", ""))
        return fechas
    except Exception as e:
        logger.warning("No se pudo leer %s: %s — se usarán todos los feriados", _FERIADOS_IGNORAR_PATH, e)
        return set()

def _calcular_dias_habiles_mes():
    """Calcula días hábiles (L-S, excluyendo feriados AR) del mes actual y transcurridos hasta hoy."""
    hoy = date.today()
    primer_dia = hoy.replace(day=1)
    # Último día del mes
    if hoy.month == 12:
        ultimo_dia = date(hoy.year + 1, 1, 1).replace(day=1)
    else:
        ultimo_dia = date(hoy.year, hoy.month + 1, 1)
    ultimo_dia = ultimo_dia - timedelta(days=1)

    ar_holidays = _holidays_lib.Argentina(years=hoy.year)
    ignorar = _cargar_feriados_ignorar()

    habiles_total = 0
    habiles_transcurridos = 0
    feriados_excluidos = []
    dia = primer_dia
    while dia <= ultimo_dia:
        es_laboral = dia.weekday() < 6  # Lunes=0 a Sábado=5
        es_feriado = es_laboral and dia in ar_holidays and dia not in ignorar
        if es_feriado:
            nombre = ar_holidays.get(dia)
            feriados_excluidos.append((dia, nombre))
            logger.info("Feriado excluido: %s — %s", dia.strftime("%Y-%m-%d"), nombre)
        elif es_laboral:
            habiles_total += 1
            if dia <= hoy:
                habiles_transcurridos += 1
        dia += timedelta(days=1)

    nombres_fer = [f"{f[0].strftime('%d/%m')} {f[1]}" for f in feriados_excluidos]
    mes_nombre = hoy.strftime("%B %Y").capitalize()
    logger.info(
        "%s: %d días hábiles (%d feriados excluidos: [%s])",
        mes_nombre, habiles_total, len(feriados_excluidos),
        ", ".join(nombres_fer) if nombres_fer else "ninguno",
    )

    return habiles_total, habiles_transcurridos

_dias_cache = {}

def get_dias_habiles():
    """Retorna (habiles, transcurridos, restantes) recalculando si cambió el día."""
    hoy = date.today()
    if hoy not in _dias_cache:
        _dias_cache.clear()  # Solo mantener el día actual
        total, trans = _calcular_dias_habiles_mes()
        trans = max(trans, 1)
        restantes = max(total - trans, 1)
        _dias_cache[hoy] = (total, trans, restantes)
    return _dias_cache[hoy]

# Backward compat — módulo-level (frozen al importar).
# Preferir get_dias_habiles() en código nuevo.
DIAS_HABILES, DIAS_TRANSCURRIDOS, DIAS_RESTANTES = get_dias_habiles()

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
