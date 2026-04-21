"""
Conexión a PostgreSQL — App DB (sellers_app_db).

Contiene los schemas de lectura-escritura: auth.* y operations.*
Lee credenciales desde variables de entorno APP_DB_*.
Datos críticos para backup (usuarios, tokens, visitas, etc).
"""
import os
import logging
import pathlib

import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# Buscar .env en la raíz del proyecto (3 niveles arriba de backend/data/app_db.py)
_env_path = pathlib.Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(_env_path)

logger = logging.getLogger(__name__)

_pool = None


def _get_pool():
    """Inicializa el pool de conexiones (lazy singleton)."""
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=os.getenv('APP_DB_HOST', 'localhost'),
            port=os.getenv('APP_DB_PORT', '5432'),
            dbname=os.getenv('APP_DB_NAME', 'sellers_app_db'),
            user=os.getenv('APP_DB_USER'),
            password=os.getenv('APP_DB_PASSWORD'),
        )
        logger.info('Pool de conexiones App DB (sellers_app_db) creado')
    return _pool


def init_pool() -> None:
    """Pre-inicializa el pool (llamar desde lifespan al arrancar)."""
    _get_pool()


def close_pool() -> None:
    """Cierra todas las conexiones del pool (llamar desde lifespan al apagar)."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
        logger.info('Pool App DB cerrado')


def get_connection():
    """Retorna conexión desde el pool."""
    return _get_pool().getconn()


def release_connection(conn) -> None:
    """Devuelve una conexión al pool."""
    if _pool is not None:
        _pool.putconn(conn)
