"""
Servicio de preventistas: listado, iniciales y lookup de ruta.
"""
import pandas as pd

from utils import to_slug


def compute_initials(nombre: str) -> str:
    """Deriva iniciales de 2 letras desde el nombre del preventista.

    Reglas:
    - 1 palabra  → primeras 2 letras de esa palabra, mayúsculas.
    - 2+ palabras → primera letra de las primeras DOS palabras, mayúsculas.
    """
    parts = nombre.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if len(parts) == 1 and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    return (nombre[:2]).upper()


def _lookup_ruta(df: pd.DataFrame, vendedor: str) -> str | None:
    """Retorna la ruta del vendedor si existe alguna columna 'ruta' o 'id_ruta' en el df.

    El DataFrame principal no incluye ruta actualmente → retorna None.
    Extendible cuando se agregue la columna.
    """
    if 'ruta' in df.columns:
        rows = df.loc[df['vendedor'] == vendedor, 'ruta'].dropna()
        if not rows.empty:
            return str(rows.iloc[0])
    return None


def get_preventistas(df: pd.DataFrame, sucursal_id: int = 1) -> list[dict]:
    """Retorna listado de preventistas para una sucursal, ordenado por nombre.

    Args:
        df: DataFrame principal (columnas: vendedor, sucursal, ...).
        sucursal_id: ID numérico de la sucursal (e.g. 1 → "1 - CASA CENTRAL").

    Returns:
        Lista de dicts con keys: nombre, slug, iniciales, ruta.
    """
    # La columna 'sucursal' tiene formato "id - NOMBRE"
    prefix = f"{sucursal_id} - "
    mask = df['sucursal'].str.startswith(prefix)
    vendedores = df.loc[mask, 'vendedor'].dropna().unique()

    result = [
        {
            'nombre': v,
            'slug': to_slug(v),
            'iniciales': compute_initials(v),
            'ruta': _lookup_ruta(df, v),
        }
        for v in sorted(vendedores)
    ]
    return result
