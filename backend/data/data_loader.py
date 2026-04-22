"""
Orquestador de datos: combina ventas y cupos de PostgreSQL.
Si no hay conexión a BD, usa datos mock como fallback.
"""
import logging
import os
from datetime import date

import pandas as pd

try:
    import psycopg2
    _EXPECTED_ERRORS = (OSError, ImportError, ValueError, psycopg2.Error)
except ImportError:
    _EXPECTED_ERRORS = (OSError, ImportError, ValueError)

from config import (
    get_dias_habiles,
    MAPEO_GENERICO_CATEGORIA, MAPEO_MARCA_GRUPO, MAPEO_DESAGREGADO_CUPO,
)

logger = logging.getLogger(__name__)

CUPOS_COBERTURA_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cupos_cobertura.csv')

# --- Daily cache for get_dataframe ---
_df_cache = None
_df_cache_date = None

# --- Daily cache for get_cobertura_dataframe ---
_cob_cache = None
_cob_cache_date = None


def _cargar_ventas_db():
    """Trae ventas del mes actual desde PostgreSQL."""
    from data.gold_db import get_connection, release_connection
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


def _cargar_supervisores_app_db() -> dict[str, str]:
    """Load preventista → supervisor mapping from operations schema (app_db).

    Returns:
        Dict mapping vendedor name → supervisor name.
        Returns empty dict on error (graceful degradation).
    """
    from data.app_db import get_connection, release_connection

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT preventista, supervisor FROM operations.preventistas_supervisores"
            )
            return {row[0]: row[1] for row in cur.fetchall()}
    finally:
        release_connection(conn)


def _mapear_cupos_desagregado(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Transform raw DW cupos rows into dashboard format.

    Maps desagregado values using MAPEO_DESAGREGADO_CUPO:
      - 'CERVEZAS'    → categoria='CERVEZAS',     grupo_marca='TOTAL_CERVEZAS'
      - 'SALTA', etc. → categoria='CERVEZAS',     grupo_marca=desagregado
      - 'AGUAS DANONE'→ categoria='AGUAS_DANONE', grupo_marca=None
      - 'MULTICCU'    → categoria='MULTICCU',     grupo_marca=None

    Args:
        df_raw: DataFrame with columns vendedor, sucursal, grupo_marca (raw desagregado), cupo

    Returns:
        DataFrame with columns: vendedor, sucursal, categoria, grupo_marca, cupo (int)
    """
    df = df_raw.copy()

    # Apply MAPEO_DESAGREGADO_CUPO: desagregado → (categoria, grupo_marca)
    df['_mapped'] = df['grupo_marca'].map(MAPEO_DESAGREGADO_CUPO)

    # Drop rows with no mapping (unknown desagregado values)
    df = df[df['_mapped'].notna()].copy()

    df['categoria'] = df['_mapped'].apply(lambda x: x[0])
    df['grupo_marca'] = df['_mapped'].apply(lambda x: x[1])  # None for MULTICCU/AGUAS_DANONE

    df = df.drop(columns=['_mapped'])

    # Round and convert cupo to int (DW gives NUMERIC(15,8))
    df['cupo'] = df['cupo'].fillna(0).round(0).astype(int)

    return df[['vendedor', 'sucursal', 'categoria', 'grupo_marca', 'cupo']]


def _cargar_cupos_db() -> pd.DataFrame | None:
    """Load sales quotas from gold.fact_cupos (DW) for the current month.

    Joins with dim_cliente to resolve preventista name per route.
    Applies category/group mapping via MAPEO_DESAGREGADO_CUPO.

    Returns:
        DataFrame with columns: vendedor, sucursal, supervisor, categoria, grupo_marca, cupo
        Returns None on connection/query errors (caller handles fallback).
    """
    from data.gold_db import get_connection, release_connection
    from data.queries import query_cupos_mes

    hoy = date.today()
    periodo = hoy.strftime('%Y-%m')

    conn = get_connection()
    try:
        df_raw = query_cupos_mes(conn, periodo)
    finally:
        release_connection(conn)

    if df_raw.empty:
        logger.warning('Query de cupos retornó vacío para periodo %s', periodo)
        return None

    # Map desagregado → (categoria, grupo_marca)
    df = _mapear_cupos_desagregado(df_raw)

    # Load supervisor mapping from app_db
    try:
        sup_map = _cargar_supervisores_app_db()
    except Exception as exc:
        logger.warning('No se pudo cargar supervisores desde app_db: %s', exc)
        sup_map = {}

    df['supervisor'] = df['vendedor'].map(sup_map).fillna('SIN SUPERVISOR')

    logger.info('Cupos cargados desde DW (%d filas, periodo %s)', len(df), periodo)
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
    Carga datos desde PostgreSQL (ventas + cupos DW) o mock como fallback.
    Columnas: vendedor, supervisor, categoria, grupo_marca, ventas, cupo,
              falta, tendencia, pct_tendencia, vta_diaria_necesaria
    """
    try:
        # 1. Ventas desde BD Gold
        df_ventas = _cargar_ventas_db()
        if df_ventas.empty:
            raise ValueError('Query de ventas retornó vacío')

        # 2. Mapear categorías y agrupar
        df_ventas = _mapear_categorias(df_ventas)

        # 3. Cupos desde DW (gold.fact_cupos) + supervisor desde app_db
        df_cupos = _cargar_cupos_db()

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

            # Asignar supervisor: para filas sin match en cupos, buscar en el df de cupos
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

        logger.info('Datos cargados desde PostgreSQL DW (%d filas)', len(df))
        return df

    except _EXPECTED_ERRORS as e:
        # Errores esperados: sin conexión BD, query vacío
        logger.warning('Fallback a datos mock (error de datos): %s', e)
        from data.mock_data import get_mock_dataframe
        return get_mock_dataframe()
    except Exception:
        # Bugs de programación: no silenciar
        logger.exception('Error inesperado cargando datos')
        raise


# ============================================================
# Cobertura
# ============================================================

def _cargar_cobertura_db():
    """Trae cobertura del mes actual desde PostgreSQL."""
    from data.gold_db import get_connection, release_connection
    from data.queries import query_cobertura_mes

    hoy = date.today()
    fecha_desde = hoy.replace(day=1)

    conn = get_connection()
    try:
        df = query_cobertura_mes(conn, fecha_desde)
    finally:
        release_connection(conn)

    df['cobertura'] = pd.to_numeric(df['cobertura'], errors='coerce').fillna(0).astype(int)
    return df


def _cargar_cupos_cobertura_csv():
    """
    Carga cupos de cobertura desde CSV.
    Columnas esperadas: vendedor, marca, sucursal, cupo_cobertura
    """
    if not os.path.exists(CUPOS_COBERTURA_CSV_PATH):
        logger.warning('Archivo de cupos cobertura no encontrado: %s', CUPOS_COBERTURA_CSV_PATH)
        return None

    return pd.read_csv(CUPOS_COBERTURA_CSV_PATH)


def _cargar_supervisor_lookup() -> pd.DataFrame:
    """Carga mapeo vendedor → supervisor desde operations.preventistas_supervisores (app_db).

    Returns:
        DataFrame with columns: vendedor, supervisor
    """
    try:
        sup_map = _cargar_supervisores_app_db()
    except Exception as exc:
        logger.warning('No se pudo cargar supervisores para lookup: %s', exc)
        return pd.DataFrame(columns=['vendedor', 'supervisor'])

    if not sup_map:
        return pd.DataFrame(columns=['vendedor', 'supervisor'])

    return pd.DataFrame(
        [(k, v) for k, v in sup_map.items()],
        columns=['vendedor', 'supervisor'],
    )


def get_cobertura_dataframe():
    """Retorna DataFrame de cobertura cacheado por día."""
    global _cob_cache, _cob_cache_date
    hoy = date.today()
    if _cob_cache is None or _cob_cache_date != hoy:
        logger.info('Cargando datos de cobertura (fecha: %s)', hoy)
        _cob_cache = _load_cobertura_dataframe()
        _cob_cache_date = hoy
    return _cob_cache


def _load_cobertura_dataframe():
    """
    Carga cobertura desde PostgreSQL + CSV de cupos cobertura.
    Solo mantiene marcas que aparecen en el CSV de cupos.

    Columnas: vendedor, sucursal, supervisor, marca, cobertura, cupo_cobertura, pct_cobertura
    """
    try:
        # 1. Cobertura desde BD
        df_cob = _cargar_cobertura_db()
        if df_cob.empty:
            raise ValueError('Query de cobertura retornó vacío')

        # 2. Cupos cobertura desde CSV
        df_cupos = _cargar_cupos_cobertura_csv()
        if df_cupos is None or df_cupos.empty:
            raise ValueError('CSV de cupos cobertura vacío o no encontrado')

        # 3. Merge: LEFT desde cupos (solo marcas con cupo)
        merge_keys = ['vendedor', 'sucursal', 'marca']
        df = df_cupos.merge(
            df_cob[['vendedor', 'sucursal', 'marca', 'cobertura']],
            on=merge_keys,
            how='left',
        )

        # Rellenar faltantes
        df['cobertura'] = df['cobertura'].fillna(0).astype(int)
        df['cupo_cobertura'] = df['cupo_cobertura'].fillna(0).astype(int)

        # 4. Calcular porcentaje
        df['pct_cobertura'] = df.apply(
            lambda row: (row['cobertura'] / row['cupo_cobertura'] * 100)
            if row['cupo_cobertura'] > 0 else 0.0,
            axis=1,
        )

        # 5. Asignar supervisor desde operations.preventistas_supervisores
        sup_lookup = _cargar_supervisor_lookup()
        df = df.merge(sup_lookup, on=['vendedor'], how='left')
        df['supervisor'] = df['supervisor'].fillna('SIN SUPERVISOR')

        logger.info('Datos de cobertura cargados (%d filas)', len(df))
        return df

    except _EXPECTED_ERRORS as e:
        logger.warning('Error cargando cobertura: %s', e)
        return pd.DataFrame(columns=[
            'vendedor', 'sucursal', 'supervisor', 'marca',
            'cobertura', 'cupo_cobertura', 'pct_cobertura',
        ])
    except Exception:
        logger.exception('Error inesperado cargando cobertura')
        raise
