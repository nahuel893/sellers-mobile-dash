"""
Procesa los archivos Excel de cupos y genera data/cupos.csv.

Lee los 3 archivos Excel de cupos_badie:
  - Cupo_CC_Valle.xlsx (sucursal 1 - CASA CENTRAL)
  - Cupo_SUCURSALES.xlsx (sucursales 3-15)
  - Cupo_GUEMES.xlsx (sucursal 16)

Cruza con dim_cliente (id_ruta_fv1 + id_sucursal) para obtener
el nombre del vendedor, y mapea DESAGREGADO → (categoria, grupo_marca).

Uso:
    python scripts/procesar_cupos.py
"""
import os
import sys
import re

import pandas as pd

# Agregar raíz del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import MAPEO_DESAGREGADO_CUPO, NORMALIZAR_VENDEDOR, VENDEDORES_EXCLUIR
from src.data.db import get_connection

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'cupos_badie')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cupos.csv')
SUPERVISORES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'supervisores.xlsx')


def _extraer_id_sucursal(texto):
    """Extrae el ID numérico de '3 - SUCURSAL CAFAYATE' → 3."""
    match = re.match(r'(\d+)', str(texto).strip())
    return int(match.group(1)) if match else None


def _cargar_lookup_vendedores():
    """Carga mapeo (id_sucursal, id_ruta_fv1) → des_personal_fv1 desde dim_cliente."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT DISTINCT id_sucursal, id_ruta_fv1, des_personal_fv1
        FROM gold.dim_cliente
        WHERE id_ruta_fv1 IS NOT NULL
          AND des_personal_fv1 IS NOT NULL
    """, conn)
    conn.close()

    # Crear dict (sucursal, ruta) → vendedor
    lookup = {}
    for _, row in df.iterrows():
        key = (int(row['id_sucursal']), int(row['id_ruta_fv1']))
        lookup[key] = row['des_personal_fv1']
    return lookup


def _cargar_lookup_sucursales():
    """Carga mapeo id_sucursal → 'id - nombre' desde dim_sucursal."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT id_sucursal, descripcion
        FROM gold.dim_sucursal
    """, conn)
    conn.close()

    lookup = {}
    for _, row in df.iterrows():
        lookup[int(row['id_sucursal'])] = f"{int(row['id_sucursal'])} - {row['descripcion']}"
    return lookup


def _cargar_lookup_supervisores():
    """Carga mapeo vendedor → supervisor desde supervisores.xlsx.

    El Excel no tiene headers; la primera fila de datos aparece como
    nombres de columna. Se lee con header=None para capturar todo.
    """
    if not os.path.exists(SUPERVISORES_PATH):
        print("  AVISO: supervisores.xlsx no encontrado, se usará 'SIN SUPERVISOR'")
        return {}

    df = pd.read_excel(SUPERVISORES_PATH, header=None, names=['vendedor', 'supervisor'])
    lookup = {}
    for _, row in df.iterrows():
        lookup[str(row['vendedor']).strip().upper()] = str(row['supervisor']).strip().upper()
    return lookup


def _leer_excel_cc_valle():
    """Lee Cupo_CC_Valle.xlsx - tiene Descripción = vendedor."""
    path = os.path.join(BASE_DIR, 'Cupo_CC_Valle.xlsx')
    df = pd.read_excel(path)

    # Normalizar nombres de columnas (encoding issues con Código/Descripción)
    cols = df.columns.tolist()
    col_map = {}
    for c in cols:
        cl = c.lower()
        if 'digo' in cl or 'codigo' in cl:
            col_map[c] = 'codigo'
        elif 'descripci' in cl:
            col_map[c] = 'descripcion'
        else:
            col_map[c] = c
    df = df.rename(columns=col_map)

    df['Sucursal'] = df['Sucursal'].replace('VALLE SALTA', '1 - CASA CENTRAL')
    df['id_sucursal'] = df['Sucursal'].apply(_extraer_id_sucursal)
    df['codigo'] = df['codigo'].astype(int)

    return df[['id_sucursal', 'codigo', 'descripcion', 'DESAGREGADO', 'Cupo']].copy()


def _leer_excel_sucursales():
    """Lee Cupo_SUCURSALES.xlsx."""
    path = os.path.join(BASE_DIR, 'Cupo_SUCURSALES.xlsx')
    df = pd.read_excel(path)

    cols = df.columns.tolist()
    col_map = {}
    for c in cols:
        cl = c.lower()
        if 'digo' in cl or 'codigo' in cl:
            col_map[c] = 'codigo'
        elif 'descripci' in cl:
            col_map[c] = 'descripcion'
        else:
            col_map[c] = c
    df = df.rename(columns=col_map)

    df['id_sucursal'] = df['SUCURSAL'].apply(_extraer_id_sucursal)
    df['codigo'] = df['codigo'].astype(int)

    return df[['id_sucursal', 'codigo', 'descripcion', 'DESAGREGADO', 'Cupo']].copy()


def _leer_excel_guemes():
    """Lee Cupo_GUEMES.xlsx."""
    path = os.path.join(BASE_DIR, 'Cupo_GUEMES.xlsx')
    df = pd.read_excel(path)

    cols = df.columns.tolist()
    col_map = {}
    for c in cols:
        cl = c.lower()
        if 'digo' in cl or 'codigo' in cl:
            col_map[c] = 'codigo'
        elif 'descripci' in cl:
            col_map[c] = 'descripcion'
        else:
            col_map[c] = c
    df = df.rename(columns=col_map)

    df['id_sucursal'] = df['SUCURSAL'].apply(_extraer_id_sucursal)
    df['codigo'] = df['codigo'].dropna().astype(int)

    return df[['id_sucursal', 'codigo', 'descripcion', 'DESAGREGADO', 'Cupo']].dropna(subset=['codigo']).copy()


def main():
    print("Cargando lookup de vendedores desde dim_cliente...")
    lookup = _cargar_lookup_vendedores()
    print(f"  {len(lookup)} pares (sucursal, ruta) cargados")

    print("Cargando lookup de sucursales desde dim_sucursal...")
    lookup_suc = _cargar_lookup_sucursales()
    print(f"  {len(lookup_suc)} sucursales cargadas")

    print("Cargando lookup de supervisores...")
    lookup_sup = _cargar_lookup_supervisores()
    print(f"  {len(lookup_sup)} mapeos vendedor→supervisor cargados")

    print("\nLeyendo archivos Excel...")
    df_cc = _leer_excel_cc_valle()
    print(f"  CC_Valle: {len(df_cc)} filas")
    df_suc = _leer_excel_sucursales()
    print(f"  SUCURSALES: {len(df_suc)} filas")
    df_gue = _leer_excel_guemes()
    print(f"  GUEMES: {len(df_gue)} filas")

    # Unir todos
    df = pd.concat([df_cc, df_suc, df_gue], ignore_index=True)
    print(f"\nTotal filas combinadas: {len(df)}")

    # Descartar filas con sucursal o código faltante
    df = df.dropna(subset=['id_sucursal', 'codigo'])
    df['id_sucursal'] = df['id_sucursal'].astype(int)
    df['codigo'] = df['codigo'].astype(int)

    # Resolver vendedor via lookup (sucursal, ruta) → dim_cliente.des_personal_fv1
    df['vendedor'] = df.apply(
        lambda row: lookup.get((row['id_sucursal'], row['codigo'])),
        axis=1,
    )

    # Reportar rutas sin vendedor
    sin_vendedor = df[df['vendedor'].isna()]
    if len(sin_vendedor) > 0:
        rutas_faltantes = sin_vendedor[['id_sucursal', 'codigo', 'descripcion']].drop_duplicates()
        print(f"\nATENCION: {len(rutas_faltantes)} rutas sin vendedor en dim_cliente:")
        for _, r in rutas_faltantes.iterrows():
            print(f"  sucursal={int(r['id_sucursal'])}, ruta={int(r['codigo'])}, desc={r['descripcion']}")

    df = df.dropna(subset=['vendedor'])

    # Normalizar nombres de vendedor (dim_cliente → dim_vendedor)
    df['vendedor'] = df['vendedor'].replace(NORMALIZAR_VENDEDOR)

    # Excluir vendedores que no son preventistas
    df = df[~df['vendedor'].isin(VENDEDORES_EXCLUIR)]

    # Filtrar solo DESAGREGADO que nos interesan
    df = df[df['DESAGREGADO'].isin(MAPEO_DESAGREGADO_CUPO.keys())].copy()

    # Mapear DESAGREGADO → (categoria, grupo_marca)
    df['categoria'] = df['DESAGREGADO'].map(lambda x: MAPEO_DESAGREGADO_CUPO[x][0])
    df['grupo_marca'] = df['DESAGREGADO'].map(lambda x: MAPEO_DESAGREGADO_CUPO[x][1])

    # Agregar cupos por vendedor + sucursal + categoria + grupo_marca
    # (un vendedor puede tener múltiples rutas dentro de una sucursal)
    df_cupos = (
        df.groupby(['vendedor', 'id_sucursal', 'categoria', 'grupo_marca'], as_index=False, dropna=False)
        ['Cupo'].sum()
    )
    df_cupos = df_cupos.rename(columns={'Cupo': 'cupo'})
    df_cupos['cupo'] = df_cupos['cupo'].round(0).astype(int)

    # Mapear id_sucursal → sucursal string ("id - nombre")
    df_cupos['sucursal'] = df_cupos['id_sucursal'].map(lookup_suc)

    # Asignar supervisor desde lookup (vendedor → supervisor)
    df_cupos['supervisor'] = df_cupos['vendedor'].str.upper().map(lookup_sup).fillna('SIN SUPERVISOR')

    # Ordenar y guardar
    df_cupos = df_cupos[['vendedor', 'sucursal', 'supervisor', 'categoria', 'grupo_marca', 'cupo']]
    df_cupos = df_cupos.sort_values(['sucursal', 'vendedor', 'categoria', 'grupo_marca']).reset_index(drop=True)

    df_cupos.to_csv(OUTPUT_PATH, index=False)
    print(f"\nCSV generado: {OUTPUT_PATH}")
    print(f"  {len(df_cupos)} filas")
    print(f"  {df_cupos['vendedor'].nunique()} vendedores")
    print(f"  Categorías: {df_cupos['categoria'].unique().tolist()}")
    print(f"\nMuestra:")
    print(df_cupos.head(15).to_string(index=False))


if __name__ == '__main__':
    main()
