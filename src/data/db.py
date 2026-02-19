"""
Conexión a PostgreSQL (capa Gold).
Credenciales via variables de entorno o archivo .env
"""
import os
import logging

import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_pool = None


def _get_pool():
    """Inicializa el pool de conexiones (lazy singleton)."""
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            dbname=os.getenv('DB_NAME', 'gold_db'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
        )
        logger.info('Pool de conexiones PostgreSQL creado')
    return _pool


def get_connection():
    """Retorna conexión desde el pool."""
    return _get_pool().getconn()


def release_connection(conn):
    """Devuelve una conexión al pool."""
    if _pool is not None:
        _pool.putconn(conn)
