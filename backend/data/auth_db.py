"""
Conexión a PostgreSQL (capa Auth / seller_dashboard_db).
Credenciales via variables de entorno o archivo .env.

Fallback: si AUTH_DB_* no están seteadas, usa las mismas que el gold DB
para mantener compatibilidad en setups de un solo servidor (dev).
"""
import os
import logging
import pathlib

import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# Buscar .env en la raíz del proyecto (3 niveles arriba de backend/data/auth_db.py)
_env_path = pathlib.Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(_env_path)

logger = logging.getLogger(__name__)

_auth_pool = None


def _get_auth_pool():
    """Inicializa el pool de conexiones para auth DB (lazy singleton)."""
    global _auth_pool
    if _auth_pool is None:
        _auth_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=os.getenv('AUTH_DB_HOST', os.getenv('DB_HOST', 'localhost')),
            port=os.getenv('AUTH_DB_PORT', os.getenv('DB_PORT', '5432')),
            dbname=os.getenv('AUTH_DB_NAME', 'seller_dashboard_db'),
            user=os.getenv('AUTH_DB_USER', os.getenv('DB_USER')),
            password=os.getenv('AUTH_DB_PASSWORD', os.getenv('DB_PASSWORD')),
        )
        logger.info('Pool de conexiones auth DB (seller_dashboard_db) creado')
    return _auth_pool


def get_auth_connection():
    """Retorna conexión desde el pool auth."""
    return _get_auth_pool().getconn()


def release_auth_connection(conn):
    """Devuelve una conexión al pool auth."""
    if _auth_pool is not None:
        _auth_pool.putconn(conn)
