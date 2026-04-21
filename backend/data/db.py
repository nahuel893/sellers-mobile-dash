"""
DEPRECATED — thin re-export para compatibilidad.

Usar data.gold_db para conexiones a la capa Gold DW (medallion_db).
Usar data.app_db para conexiones a la App DB (sellers_app_db).

Este módulo re-exporta las funciones de gold_db para no romper
código legacy que importaba desde data.db.
"""
import warnings as _warnings

_warnings.warn(
    "data.db está deprecado. Usar data.gold_db para Gold DW o data.app_db para App DB.",
    DeprecationWarning,
    stacklevel=2,
)

from data.gold_db import (  # noqa: F401, E402
    get_connection,
    release_connection,
    init_pool,
    close_pool,
)
