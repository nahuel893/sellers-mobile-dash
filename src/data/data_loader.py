"""
Orquestador de datos: combina ventas de PostgreSQL con cupos de CSV.
Si no hay conexión a BD, usa datos mock como fallback.
"""
import os
import logging
from datetime import date

import pandas as pd

from config import (
    DIAS_HABILES, DIAS_TRANSCURRIDOS, DIAS_RESTANTES,
    MAPEO_GENERICO_CATEGORIA, GRUPOS_MARCA,
)

logger = logging.getLogger(__name__)

CUPOS_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cupos.csv')


def _cargar_ventas_db():
    """Trae ventas del mes actual desde PostgreSQL."""
    from src.data.db import get_connection
    from src.data.queries import query_ventas_mes

    hoy = date.today()
    fecha_desde = hoy.replace(day=1)
    fecha_hasta = hoy

    conn = get_connection()
    try:
        df = query_ventas_mes(conn, fecha_desde, fecha_hasta)
    finally:
        conn.close()

    return df


def _mapear_categorias(df):
    """
    Mapea genérico de BD → categoría del dashboard.
    Para CERVEZAS mantiene la marca como grupo_marca.
    Para MULTICCU y AGUAS_DANONE agrupa todo (grupo_marca=None).
    """
    df = df.copy()
    df['categoria'] = df['generico'].map(MAPEO_GENERICO_CATEGORIA)
    # Descartar genéricos que no mapeamos
    df = df.dropna(subset=['categoria'])

    # --- CERVEZAS: marca → grupo_marca ---
    mask_cervezas = df['categoria'] == 'CERVEZAS'
    df.loc[mask_cervezas, 'grupo_marca'] = df.loc[mask_cervezas, 'marca'].str.upper()

    # Marcas que no son un grupo conocido van a MULTICERVEZAS (por ahora)
    grupos_set = set(GRUPOS_MARCA)
    mask_desconocida = mask_cervezas & ~df['grupo_marca'].isin(grupos_set)
    df.loc[mask_desconocida, 'grupo_marca'] = 'MULTICERVEZAS'

    # Re-agregar por grupo_marca (varias marcas pueden caer en MULTICERVEZAS)
    df_cervezas = (
        df[mask_cervezas]
        .groupby(['vendedor', 'categoria', 'grupo_marca'], as_index=False)
        ['ventas'].sum()
    )

    # --- MULTICCU / AGUAS_DANONE: agrupar todo por vendedor ---
    mask_otros = ~mask_cervezas
    df_otros = (
        df[mask_otros]
        .groupby(['vendedor', 'categoria'], as_index=False)
        ['ventas'].sum()
    )
    df_otros['grupo_marca'] = None

    return pd.concat([df_cervezas, df_otros], ignore_index=True)


def _cargar_cupos_csv():
    """
    Carga cupos y supervisores desde CSV.
    Columnas esperadas: vendedor, supervisor, categoria, grupo_marca, cupo
    """
    if not os.path.exists(CUPOS_CSV_PATH):
        logger.warning('Archivo de cupos no encontrado: %s', CUPOS_CSV_PATH)
        return None

    df = pd.read_csv(CUPOS_CSV_PATH)
    # Normalizar grupo_marca vacío a None
    df['grupo_marca'] = df['grupo_marca'].where(df['grupo_marca'].notna(), None)
    return df


def _calcular_columnas_derivadas(df):
    """Calcula falta, tendencia, pct_tendencia, vta_diaria_necesaria."""
    df = df.copy()
    df['falta'] = df['cupo'] - df['ventas']
    df['tendencia'] = (df['ventas'] * DIAS_HABILES / DIAS_TRANSCURRIDOS).round(0)
    df['pct_tendencia'] = (
        (df['tendencia'] / df['cupo'].replace(0, float('nan'))) * 100
    ).fillna(0).round(0).astype(int)
    df['vta_diaria_necesaria'] = (df['falta'] / DIAS_RESTANTES).round(1)
    return df


def get_dataframe():
    """
    Retorna DataFrame con la misma estructura que mock_data.
    Columnas: vendedor, supervisor, categoria, grupo_marca, ventas, cupo,
              falta, tendencia, pct_tendencia, vta_diaria_necesaria

    Intenta conectar a PostgreSQL + CSV de cupos.
    Si falla, cae a datos mock.
    """
    try:
        # 1. Ventas desde BD
        df_ventas = _cargar_ventas_db()
        if df_ventas.empty:
            raise ValueError('Query de ventas retornó vacío')

        # 2. Mapear categorías y agrupar
        df_ventas = _mapear_categorias(df_ventas)

        # 3. Cupos desde CSV
        df_cupos = _cargar_cupos_csv()
        if df_cupos is None:
            raise FileNotFoundError('No hay archivo de cupos')

        # 4. Merge ventas + cupos
        merge_keys = ['vendedor', 'categoria', 'grupo_marca']
        df = df_ventas.merge(
            df_cupos[['vendedor', 'supervisor', 'categoria', 'grupo_marca', 'cupo']],
            on=merge_keys,
            how='inner',
        )

        # 5. Calcular columnas derivadas
        df = _calcular_columnas_derivadas(df)

        logger.info('Datos cargados desde PostgreSQL + CSV (%d filas)', len(df))
        return df

    except Exception as e:
        logger.warning('Fallback a datos mock: %s', e)
        from src.data.mock_data import get_mock_dataframe
        return get_mock_dataframe()
