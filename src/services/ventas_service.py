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


def get_supervisores(df):
    """Lista de supervisores disponibles."""
    return sorted(df['supervisor'].unique().tolist())


def get_vendedores_por_supervisor(df, supervisor):
    """Lista de vendedores de un supervisor."""
    return sorted(
        df[df['supervisor'] == supervisor]['vendedor'].unique().tolist()
    )


def get_datos_vendedor(df, vendedor):
    """Datos de un vendedor específico."""
    return df[df['vendedor'] == vendedor].copy()


def get_resumen_vendedor(df, vendedor):
    """Resumen total de un vendedor (todas las marcas)."""
    datos = get_datos_vendedor(df, vendedor)
    total_ventas = datos['ventas'].sum()
    total_cupo = datos['cupo'].sum()
    total_falta = datos['falta'].sum()
    total_tendencia = datos['tendencia'].sum()
    pct_total = round(total_tendencia / total_cupo * 100) if total_cupo > 0 else 0
    return {
        'vendedor': vendedor,
        'ventas': int(total_ventas),
        'cupo': int(total_cupo),
        'falta': int(total_falta),
        'tendencia': int(total_tendencia),
        'pct_tendencia': pct_total,
    }
