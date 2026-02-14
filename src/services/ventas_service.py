"""
Capa de negocio: cálculos de tendencia, filtros y agregaciones.
"""
import pandas as pd

from config import DIAS_HABILES, DIAS_TRANSCURRIDOS, DIAS_RESTANTES


def calcular_tendencia(ventas, dias_trans=DIAS_TRANSCURRIDOS, dias_hab=DIAS_HABILES):
    """Proyección de ventas a fin de mes."""
    if dias_trans == 0:
        return 0
    return round(ventas * dias_hab / dias_trans)


def calcular_pct_tendencia(ventas, cupo, dias_trans=DIAS_TRANSCURRIDOS, dias_hab=DIAS_HABILES):
    """% de tendencia vs cupo."""
    if cupo == 0:
        return 0
    tendencia = calcular_tendencia(ventas, dias_trans, dias_hab)
    return round(tendencia / cupo * 100)


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
        total_cupo = int(fila_total.iloc[0]['cupo'])
    else:
        total_cupo = int(datos_marcas['cupo'].sum())

    total_falta = total_cupo - int(total_ventas)
    pct_total = round(total_tendencia / total_cupo * 100) if total_cupo > 0 else 0
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
    agg['tendencia'] = agg['ventas'].apply(lambda v: calcular_tendencia(v))
    agg['pct_tendencia'] = agg.apply(
        lambda row: calcular_pct_tendencia(row['ventas'], row['cupo']),
        axis=1,
    )
    return agg


def get_datos_sucursal(df, sucursal, categoria='CERVEZAS'):
    """Datos agregados de toda la sucursal, por grupo_marca."""
    mask = (df['sucursal'] == sucursal) & (df['categoria'] == categoria)
    return _agregar_por_grupo_marca(df, mask, categoria)


def get_resumen_sucursal(df, sucursal, categoria='CERVEZAS'):
    """Resumen total de una sucursal para una categoría."""
    datos = get_datos_sucursal(df, sucursal, categoria)
    return _resumen_desde_datos(datos, categoria)
