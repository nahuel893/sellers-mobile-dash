"""
Conexión a PostgreSQL (capa Gold).
Credenciales via variables de entorno o archivo .env
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Retorna conexión a PostgreSQL usando variables de entorno."""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        dbname=os.getenv('DB_NAME', 'gold_db'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
    )
