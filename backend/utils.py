"""Utilidades compartidas del backend."""
from urllib.parse import unquote

from services.ventas_service import get_sucursales


def to_slug(nombre):
    """Convierte nombre a slug URL-safe: 'FACUNDO CACERES' -> 'FACUNDO-CACERES'.

    Preserva guiones literales codificándolos como %2D,
    para que from_slug pueda distinguirlos de guiones-como-espacios.
    """
    s = nombre.strip()
    s = s.replace('-', '%2D')
    s = s.replace(' ', '-')
    return s


def from_slug(slug):
    """Convierte slug a nombre: 'FACUNDO-CACERES' -> 'FACUNDO CACERES'.

    Reverso de to_slug: guiones → espacios, %2D → guión literal.
    """
    s = slug.replace('-', ' ')
    s = unquote(s)  # %2D -> -
    return s


def find_sucursal(df, suc_id):
    """Busca sucursal por ID numérico. Retorna string completo o None."""
    for s in get_sucursales(df):
        if s.split(' - ')[0] == str(suc_id):
            return s
    return None
