"""
Conexión a PostgreSQL — Gold Data Warehouse (medallion_db).

Lee credenciales desde variables de entorno GOLD_DB_*.
Solo lectura desde la app — datos regenerables via ETL.
"""
import os
import logging
import pathlib

import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# Buscar .env en la raíz del proyecto (3 niveles arriba de backend/data/gold_db.py)
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
            host=os.getenv('GOLD_DB_HOST', 'localhost'),
            port=os.getenv('GOLD_DB_PORT', '5432'),
            dbname=os.getenv('GOLD_DB_NAME', 'medallion_db'),
            user=os.getenv('GOLD_DB_USER'),
            password=os.getenv('GOLD_DB_PASSWORD'),
        )
        logger.info('Pool de conexiones Gold DB (medallion_db) creado')
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
        logger.info('Pool Gold DB cerrado')


def get_connection():
    """Retorna conexión desde el pool."""
    return _get_pool().getconn()


def release_connection(conn) -> None:
    """Devuelve una conexión al pool."""
    if _pool is not None:
        _pool.putconn(conn)
