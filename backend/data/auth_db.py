"""
DEPRECATED — thin compatibility shim para código que importa
get_auth_connection / release_auth_connection.

Usar data.app_db directamente en código nuevo.

Este módulo mantiene su propio singleton _auth_pool apuntando a
sellers_app_db (APP_DB_*) para que los tests existentes que
reemplazan _auth_pool directamente sigan funcionando sin cambios.
"""
import os
import logging
import pathlib

import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

_env_path = pathlib.Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(_env_path)

logger = logging.getLogger(__name__)

_auth_pool = None


def _get_auth_pool():
    """Inicializa el pool de conexiones para auth/app DB (lazy singleton)."""
    global _auth_pool
    if _auth_pool is None:
        _auth_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=os.getenv('APP_DB_HOST', 'localhost'),
            port=os.getenv('APP_DB_PORT', '5432'),
            dbname=os.getenv('APP_DB_NAME', 'sellers_app_db'),
            user=os.getenv('APP_DB_USER'),
            password=os.getenv('APP_DB_PASSWORD'),
        )
        logger.info('Pool de conexiones Auth/App DB (sellers_app_db) creado [auth_db shim]')
    return _auth_pool


def get_auth_connection():
    """Retorna conexión desde el pool auth/app."""
    return _get_auth_pool().getconn()


def release_auth_connection(conn) -> None:
    """Devuelve una conexión al pool auth/app."""
    if _auth_pool is not None:
        _auth_pool.putconn(conn)
