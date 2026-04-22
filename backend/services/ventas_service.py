"""
Capa de negocio: cálculos de tendencia, filtros y agregaciones.
"""
from collections import defaultdict
from datetime import date, timedelta

import pandas as pd

from config import get_dias_habiles, MAPEO_MARCA_GRUPO


def calcular_tendencia(ventas, dias_trans=None, dias_hab=None):
    """Proyección de ventas a fin de mes."""
    if dias_trans is None or dias_hab is None:
        _hab, _trans, _ = get_dias_habiles()
        dias_trans = dias_trans if dias_trans is not None else _trans
        dias_hab = dias_hab if dias_hab is not None else _hab
    if dias_trans == 0:
        return 0
    return ventas * dias_hab / dias_trans


def calcular_pct_tendencia(ventas, cupo, dias_trans=None, dias_hab=None):
    """% de tendencia vs cupo."""
    if cupo == 0:
        return 0
    tendencia = calcular_tendencia(ventas, dias_trans, dias_hab)
    return tendencia / cupo * 100


def get_sucursales(df):
    """Lista de sucursales disponibles, ordenadas por ID numérico."""
    sucursales = df['sucursal'].dropna().unique().tolist()
    return sorted(sucursales, key=lambda s: int(s.split(' - ')[0]))


def get_supervisores(df, sucursal=None):
    """Lista de supervisores disponibles, opcionalmente filtrados por sucursal."""
    if sucursal:
        df = df[df['sucursal'] == sucursal]
    return sorted(df['supervisor'].unique().tolist())


def get_vendedores_por_supervisor(df, supervisor, sucursal=None):
    """Lista de vendedores de un supervisor, opcionalmente filtrados por sucursal."""
    mask = df['supervisor'] == supervisor
    if sucursal:
        mask = mask & (df['sucursal'] == sucursal)
    return sorted(df[mask]['vendedor'].unique().tolist())


def get_datos_vendedor(df, vendedor, categoria='CERVEZAS'):
    """Datos de un vendedor filtrados por categoría."""
    mask = (df['vendedor'] == vendedor) & (df['categoria'] == categoria)
    return df[mask].copy()


def _resumen_desde_datos(datos, categoria='CERVEZAS'):
    """Calcula resumen (ventas, cupo, falta, tendencia, pct) desde un DataFrame filtrado."""
    datos_marcas = datos[datos['grupo_marca'] != 'TOTAL_CERVEZAS']
    fila_total = datos[datos['grupo_marca'] == 'TOTAL_CERVEZAS']

    total_ventas = datos_marcas['ventas'].sum()
    total_tendencia = calcular_tendencia(total_ventas)

    if not fila_total.empty and categoria == 'CERVEZAS':
        total_cupo = int(fila_total['cupo'].sum())
    else:
        total_cupo = int(datos_marcas['cupo'].sum())

    total_falta = total_cupo - int(total_ventas)
    pct_total = (total_tendencia / total_cupo * 100) if total_cupo > 0 else 0
    return {
        'ventas': int(total_ventas),
        'cupo': total_cupo,
        'falta': total_falta,
        'tendencia': int(total_tendencia),
        'pct_tendencia': pct_total,
    }


def get_resumen_vendedor(df, vendedor, categoria='CERVEZAS'):
    """Resumen total de un vendedor para una categoría."""
    datos = get_datos_vendedor(df, vendedor, categoria)
    resumen = _resumen_desde_datos(datos, categoria)
    resumen['vendedor'] = vendedor
    return resumen


def get_datos_supervisor(df, supervisor, sucursal=None, categoria='CERVEZAS'):
    """Datos agregados de todos los vendedores de un supervisor, por grupo_marca."""
    mask = (df['supervisor'] == supervisor) & (df['categoria'] == categoria)
    if sucursal:
        mask = mask & (df['sucursal'] == sucursal)
    return _agregar_por_grupo_marca(df, mask, categoria)


def get_resumen_supervisor(df, supervisor, sucursal=None, categoria='CERVEZAS'):
    """Resumen total de un supervisor para una categoría."""
    datos = get_datos_supervisor(df, supervisor, sucursal, categoria)
    return _resumen_desde_datos(datos, categoria)


def _agregar_por_grupo_marca(df, mask, categoria):
    """Agrega ventas/cupo por grupo_marca y recalcula métricas derivadas."""
    datos = df[mask].copy()
    if datos.empty:
        return pd.DataFrame(columns=[
            'grupo_marca', 'ventas', 'cupo', 'categoria',
            'falta', 'tendencia', 'pct_tendencia',
        ])
    agg = datos.groupby('grupo_marca', as_index=False, dropna=False).agg({
        'ventas': 'sum',
        'cupo': 'sum',
    })
    agg['categoria'] = categoria
    agg['falta'] = agg['cupo'] - agg['ventas']
    dias_habiles, dias_transcurridos, _ = get_dias_habiles()
    if dias_transcurridos > 0:
        agg['tendencia'] = agg['ventas'] * dias_habiles / dias_transcurridos
    else:
        agg['tendencia'] = 0
    agg['pct_tendencia'] = (
        (agg['tendencia'] / agg['cupo'].replace(0, float('nan'))) * 100
    ).fillna(0)
    return agg


def get_sparkline_vendedor(conn, vendedor: str | None, dias: int = 18,
                           categoria: str = 'CERVEZAS', id_sucursal: int = 1) -> dict:
    """Retorna serie de ventas diarias por grupo_marca para el sparkline.

    Args:
        conn: conexión psycopg2 (o mock). Debe soportar cursor como context manager.
        vendedor: nombre del vendedor; None = agregado de sucursal (casa central).
        dias: días hacia atrás desde hoy (default 18, máx 90).
        categoria: categoría de artículo a filtrar (default CERVEZAS → generico).
        id_sucursal: ID de sucursal (default 1).

    Returns:
        Dict con keys: vendedor, dias, puntos (list de {fecha, por_grupo}).
    """
    from data.queries import query_sparkline_vendedor

    dias = min(dias, 90)
    rows = query_sparkline_vendedor(conn, vendedor, dias, generico=categoria, id_sucursal=id_sucursal)

    # Acumular ventas por (fecha, grupo_marca)
    totals: dict[date, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        fecha, marca, ventas = row[0], row[1], int(row[2])
        grupo = MAPEO_MARCA_GRUPO.get(str(marca).upper(), 'MULTICERVEZAS')
        totals[fecha][grupo] += ventas

    # Construir serie completa de `dias` puntos (zero-fill días sin datos)
    hoy = date.today()
    puntos = []
    for i in range(dias - 1, -1, -1):
        d = hoy - timedelta(days=i)
        por_grupo = dict(totals.get(d, {}))
        puntos.append({
            'fecha': d.isoformat(),
            'por_grupo': por_grupo,
        })

    return {
        'vendedor': vendedor if vendedor is not None else 'casa-central',
        'dias': dias,
        'puntos': puntos,
    }


def get_delta_vendedor(conn, df: 'pd.DataFrame', vendedor: str | None,
                       categoria: str = 'CERVEZAS', id_sucursal: int = 1) -> dict:
    """Calcula delta de porcentaje entre mes actual y mes anterior por grupo_marca.

    Args:
        conn: conexión psycopg2 para consultar mes anterior.
        df: DataFrame principal con datos del mes actual (ya cacheado).
        vendedor: nombre del vendedor; None = agregado (casa central).
        categoria: categoría de producto (default CERVEZAS).
        id_sucursal: ID de sucursal.

    Returns:
        Dict con keys: vendedor, deltas (list de BrandDelta-compatible dicts).
    """
    from data.queries import query_prior_month_ventas

    nombre_display = vendedor if vendedor is not None else 'casa-central'

    # --- Datos mes actual desde el DataFrame cacheado ---
    if vendedor is not None:
        mask = (df['vendedor'] == vendedor) & (df['categoria'] == categoria)
    else:
        mask = (df['categoria'] == categoria) & df['sucursal'].str.startswith(f'{id_sucursal} - ')

    df_actual = (
        df[mask & (df['grupo_marca'] != 'TOTAL_CERVEZAS')]
        .groupby('grupo_marca', dropna=False)
        .agg(pct_tendencia=('pct_tendencia', 'first'))
        .reset_index()
    )

    pct_actual_map: dict[str, float] = {
        row['grupo_marca']: round(float(row['pct_tendencia']), 1)
        for _, row in df_actual.iterrows()
        if row['grupo_marca'] is not None and not (
            isinstance(row['grupo_marca'], float) and pd.isna(row['grupo_marca'])
        )
    }

    # --- Datos mes anterior desde consulta directa ---
    try:
        prior_rows = query_prior_month_ventas(conn, vendedor=vendedor,
                                              categoria=categoria,
                                              id_sucursal=id_sucursal)
        # prior_rows: list of (grupo_marca, ventas_prior, cupo_prior)
        pct_prior_map: dict[str, float | None] = {}
        for row in prior_rows:
            grupo, ventas_p, cupo_p = row[0], int(row[1]), int(row[2])
            pct_prior_map[grupo] = round(ventas_p / cupo_p * 100, 1) if cupo_p > 0 else None
    except Exception:
        pct_prior_map = {}

    # --- Construir deltas ---
    deltas = []
    for grupo_marca, pct_act in pct_actual_map.items():
        pct_ant = pct_prior_map.get(grupo_marca)
        if pct_ant is not None:
            delta_pp: float | None = round(pct_act - pct_ant, 1)
        else:
            delta_pp = None
        deltas.append({
            'grupo_marca': grupo_marca,
            'pct_actual': pct_act,
            'pct_anterior': pct_ant,
            'delta_pp': delta_pp,
        })

    return {
        'vendedor': nombre_display,
        'deltas': deltas,
    }


def get_datos_sucursal(df, sucursal, categoria='CERVEZAS'):
    """Datos agregados de toda la sucursal, por grupo_marca."""
    mask = (df['sucursal'] == sucursal) & (df['categoria'] == categoria)
    return _agregar_por_grupo_marca(df, mask, categoria)


def get_resumen_sucursal(df, sucursal, categoria='CERVEZAS'):
    """Resumen total de una sucursal para una categoría."""
    datos = get_datos_sucursal(df, sucursal, categoria)
    return _resumen_desde_datos(datos, categoria)
