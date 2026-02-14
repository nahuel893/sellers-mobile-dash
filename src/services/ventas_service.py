"""
Capa de negocio: cálculos de tendencia, filtros y agregaciones.
"""
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


def get_resumen_vendedor(df, vendedor, categoria='CERVEZAS'):
    """Resumen total de un vendedor para una categoría.

    Para CERVEZAS: usa TOTAL_CERVEZAS cupo del Excel en vez de sumar
    cupos individuales (porque el total incluye SALTA CAUTIVA1 que no
    tiene gauge individual).
    """
    datos = get_datos_vendedor(df, vendedor, categoria)

    # Separar TOTAL_CERVEZAS (fila auxiliar solo para cupo total)
    datos_marcas = datos[datos['grupo_marca'] != 'TOTAL_CERVEZAS']
    fila_total = datos[datos['grupo_marca'] == 'TOTAL_CERVEZAS']

    total_ventas = datos_marcas['ventas'].sum()
    total_tendencia = calcular_tendencia(total_ventas)

    # Cupo: usar TOTAL_CERVEZAS si existe, sino sumar individuales
    if not fila_total.empty and categoria == 'CERVEZAS':
        total_cupo = int(fila_total.iloc[0]['cupo'])
    else:
        total_cupo = int(datos_marcas['cupo'].sum())

    total_falta = total_cupo - int(total_ventas)
    pct_total = round(total_tendencia / total_cupo * 100) if total_cupo > 0 else 0
    return {
        'vendedor': vendedor,
        'ventas': int(total_ventas),
        'cupo': total_cupo,
        'falta': total_falta,
        'tendencia': int(total_tendencia),
        'pct_tendencia': pct_total,
    }
