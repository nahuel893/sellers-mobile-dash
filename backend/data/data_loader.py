"""
Orquestador de datos: combina ventas de PostgreSQL con cupos de CSV.
Si no hay conexión a BD, usa datos mock como fallback.
"""
import os
import logging
from datetime import date

import pandas as pd

try:
    import psycopg2
    _EXPECTED_ERRORS = (OSError, ImportError, ValueError, psycopg2.Error)
except ImportError:
    _EXPECTED_ERRORS = (OSError, ImportError, ValueError)

from config import (
    get_dias_habiles,
    MAPEO_GENERICO_CATEGORIA, MAPEO_MARCA_GRUPO,
)

logger = logging.getLogger(__name__)

CUPOS_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cupos.csv')

# --- Daily cache for get_dataframe ---
_df_cache = None
_df_cache_date = None


def _cargar_ventas_db():
    """Trae ventas del mes actual desde PostgreSQL."""
    from data.db import get_connection, release_connection
    from data.queries import query_ventas_mes

    hoy = date.today()
    fecha_desde = hoy.replace(day=1)
    fecha_hasta = hoy

    conn = get_connection()
    try:
        df = query_ventas_mes(conn, fecha_desde, fecha_hasta)
    finally:
        release_connection(conn)

    # PostgreSQL devuelve Decimal → convertir a float
    df['ventas'] = pd.to_numeric(df['ventas'], errors='coerce').fillna(0)
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

    # --- CERVEZAS: marca → grupo_marca via MAPEO_MARCA_GRUPO ---
    mask_cervezas = df['categoria'] == 'CERVEZAS'
    df.loc[mask_cervezas, 'grupo_marca'] = (
        df.loc[mask_cervezas, 'marca'].str.upper().map(MAPEO_MARCA_GRUPO)
    )
    # Marcas sin mapeo van a MULTICERVEZAS
    mask_sin_mapeo = mask_cervezas & df['grupo_marca'].isna()
    df.loc[mask_sin_mapeo, 'grupo_marca'] = 'MULTICERVEZAS'

    # Re-agregar por grupo_marca (varias marcas pueden caer en MULTICERVEZAS)
    df_cervezas = (
        df[mask_cervezas]
        .groupby(['vendedor', 'sucursal', 'categoria', 'grupo_marca'], as_index=False)
        ['ventas'].sum()
    )

    # --- MULTICCU / AGUAS_DANONE: agrupar todo por vendedor ---
    mask_otros = ~mask_cervezas
    df_otros = (
        df[mask_otros]
        .groupby(['vendedor', 'sucursal', 'categoria'], as_index=False)
        ['ventas'].sum()
    )
    df_otros['grupo_marca'] = None

    return pd.concat([df_cervezas, df_otros], ignore_index=True)


def _cargar_cupos_csv():
    """
    Carga cupos y supervisores desde CSV.
    Columnas esperadas: vendedor, sucursal, supervisor, categoria, grupo_marca, cupo
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
    dias_habiles, dias_transcurridos, dias_restantes = get_dias_habiles()
    df = df.copy()
    df['falta'] = df['cupo'] - df['ventas']
    df['tendencia'] = df['ventas'] * dias_habiles / dias_transcurridos
    df['pct_tendencia'] = (
        (df['tendencia'] / df['cupo'].replace(0, float('nan'))) * 100
    ).fillna(0)
    df['vta_diaria_necesaria'] = df['falta'] / dias_restantes
    return df


def get_dataframe():
    """Retorna DataFrame cacheado por día. Recarga automáticamente al cambiar de fecha."""
    global _df_cache, _df_cache_date
    hoy = date.today()
    if _df_cache is None or _df_cache_date != hoy:
        logger.info('Cargando datos (fecha: %s)', hoy)
        _df_cache = _load_dataframe()
        _df_cache_date = hoy
    return _df_cache


def _load_dataframe():
    """
    Carga datos desde PostgreSQL + CSV de cupos (o mock como fallback).
    Columnas: vendedor, supervisor, categoria, grupo_marca, ventas, cupo,
              falta, tendencia, pct_tendencia, vta_diaria_necesaria
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

        # 4. Merge ventas + cupos (ambos tienen sucursal en formato "id - nombre")
        if df_cupos is not None and len(df_cupos) > 0:
            # Separar cupos individuales de TOTAL_CERVEZAS
            cupos_total = df_cupos[df_cupos['grupo_marca'] == 'TOTAL_CERVEZAS'].copy()
            cupos_marcas = df_cupos[df_cupos['grupo_marca'] != 'TOTAL_CERVEZAS'].copy()

            # Rellenar None/NaN con sentinel para que el merge matchee
            # (pandas no considera NaN == NaN en merges)
            _SENTINEL = '__NONE__'
            df_ventas['grupo_marca'] = df_ventas['grupo_marca'].fillna(_SENTINEL)
            cupos_marcas['grupo_marca'] = cupos_marcas['grupo_marca'].fillna(_SENTINEL)

            merge_keys = ['vendedor', 'sucursal', 'categoria', 'grupo_marca']
            df = df_ventas.merge(
                cupos_marcas[['vendedor', 'sucursal', 'supervisor', 'categoria', 'grupo_marca', 'cupo']],
                on=merge_keys,
                how='outer',
            )

            # Restaurar None y rellenar faltantes
            df['grupo_marca'] = df['grupo_marca'].replace(_SENTINEL, None)
            df['ventas'] = df['ventas'].fillna(0)
            df['cupo'] = df['cupo'].fillna(0).astype(int)

            # Asignar supervisor: para filas sin match en cupos, buscar en el CSV
            # (un vendedor puede tener ventas en categorías donde no tiene cupo)
            sup_lookup = (
                df_cupos.dropna(subset=['supervisor'])
                .drop_duplicates(subset=['vendedor', 'sucursal'])
                [['vendedor', 'sucursal', 'supervisor']]
                .rename(columns={'supervisor': '_sup_lookup'})
            )
            df = df.merge(sup_lookup, on=['vendedor', 'sucursal'], how='left')
            df['supervisor'] = df['supervisor'].fillna(df['_sup_lookup']).fillna('SIN SUPERVISOR')
            df = df.drop(columns=['_sup_lookup'])

            # Agregar filas TOTAL_CERVEZAS (para que get_resumen_vendedor use este cupo)
            if not cupos_total.empty:
                cupos_total['ventas'] = 0
                cupos_total['cupo'] = cupos_total['cupo'].astype(int)
                cupos_total['supervisor'] = cupos_total['supervisor'].fillna('SIN SUPERVISOR')
                df = pd.concat([df, cupos_total[['vendedor', 'sucursal', 'supervisor', 'categoria',
                                                  'grupo_marca', 'ventas', 'cupo']]],
                               ignore_index=True)
        else:
            df = df_ventas.copy()
            df['supervisor'] = 'SIN SUPERVISOR'
            df['cupo'] = 0

        # 5. Calcular columnas derivadas
        df = _calcular_columnas_derivadas(df)

        logger.info('Datos cargados desde PostgreSQL + CSV (%d filas)', len(df))
        return df

    except _EXPECTED_ERRORS as e:
        # Errores esperados: sin conexión BD, sin CSV, query vacío
        logger.warning('Fallback a datos mock (error de datos): %s', e)
        from data.mock_data import get_mock_dataframe
        return get_mock_dataframe()
    except Exception:
        # Bugs de programación: no silenciar
        logger.exception('Error inesperado cargando datos')
        raise
