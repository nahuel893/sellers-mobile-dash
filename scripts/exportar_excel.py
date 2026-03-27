"""
Exporta los datos del dashboard a un archivo Excel con dos hojas:
  - Volumen: ventas, cupo, falta, tendencia, %tendencia, vta/día por vendedor/categoría/marca
  - Cobertura: cobertura real vs cupo por vendedor/marca

Uso:
    python scripts/exportar_excel.py
    python scripts/exportar_excel.py -o reporte_custom.xlsx
"""
import os
import sys
import argparse
from datetime import date

import pandas as pd

# Agregar backend/ al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config import get_dias_habiles
from data.data_loader import get_dataframe, get_cobertura_dataframe


def _build_volumen(df: pd.DataFrame, dias_restantes: int) -> pd.DataFrame:
    """Construye la hoja de volumen."""
    # Excluir TOTAL_CERVEZAS y SALTA CAUTIVA1 del detalle
    mask = ~df['grupo_marca'].isin(['TOTAL_CERVEZAS', 'SALTA CAUTIVA1'])
    out = df[mask][['vendedor', 'supervisor', 'sucursal', 'categoria', 'grupo_marca',
                     'ventas', 'cupo', 'falta', 'tendencia', 'pct_tendencia']].copy()

    out['vta_dia_necesaria'] = out['falta'].clip(lower=0) / max(dias_restantes, 1)
    out['vta_dia_necesaria'] = out['vta_dia_necesaria'].apply(lambda x: int(x) if x > 0 else 0)

    out = out.rename(columns={
        'vendedor': 'Vendedor',
        'supervisor': 'Supervisor',
        'sucursal': 'Sucursal',
        'categoria': 'Categoría',
        'grupo_marca': 'Grupo Marca',
        'ventas': 'Ventas',
        'cupo': 'Cupo',
        'falta': 'Falta',
        'tendencia': 'Tendencia',
        'pct_tendencia': '% Tendencia',
        'vta_dia_necesaria': 'Vta/Día Nec.',
    })

    out = out.sort_values(['Supervisor', 'Vendedor', 'Categoría', 'Grupo Marca'])
    return out.reset_index(drop=True)


def _build_cobertura(df: pd.DataFrame) -> pd.DataFrame:
    """Construye la hoja de cobertura."""
    if df.empty:
        return pd.DataFrame()

    out = df[['vendedor', 'supervisor', 'sucursal', 'marca',
              'cobertura', 'cupo_cobertura', 'pct_cobertura']].copy()

    out['falta'] = (out['cupo_cobertura'] - out['cobertura']).clip(lower=0)

    out = out.rename(columns={
        'vendedor': 'Vendedor',
        'supervisor': 'Supervisor',
        'sucursal': 'Sucursal',
        'marca': 'Marca',
        'cobertura': 'Real',
        'cupo_cobertura': 'Cupo',
        'falta': 'Falta',
        'pct_cobertura': '% Cobertura',
    })

    out = out.sort_values(['Supervisor', 'Vendedor', 'Marca'])
    return out.reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description='Exportar dashboard a Excel')
    hoy = date.today()
    default_name = f"reporte_{hoy.strftime('%Y-%m-%d')}.xlsx"
    default_path = os.path.join(os.path.dirname(__file__), '..', 'data', default_name)
    parser.add_argument('-o', '--output', default=default_path, help='Ruta del archivo Excel')
    args = parser.parse_args()

    print("Cargando datos de volumen...")
    df_vol = get_dataframe()
    dias_habiles, dias_trans, dias_rest = get_dias_habiles()
    print(f"  {len(df_vol)} filas, {df_vol['vendedor'].nunique()} vendedores")
    print(f"  Días: {dias_habiles} hábiles, {dias_trans} transcurridos, {dias_rest} restantes")

    print("Cargando datos de cobertura...")
    df_cob = get_cobertura_dataframe()
    print(f"  {len(df_cob)} filas")

    print("Construyendo hojas...")
    vol = _build_volumen(df_vol, dias_rest)
    cob = _build_cobertura(df_cob)

    print(f"Escribiendo {args.output}...")
    with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
        vol.to_excel(writer, sheet_name='Volumen', index=False)
        if not cob.empty:
            cob.to_excel(writer, sheet_name='Cobertura', index=False)

    print(f"\nExcel generado: {args.output}")
    print(f"  Volumen: {len(vol)} filas")
    if not cob.empty:
        print(f"  Cobertura: {len(cob)} filas")


if __name__ == '__main__':
    main()
