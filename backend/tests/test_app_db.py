"""Tests for backend/data/app_db.py

Verifica que get_connection / release_connection / init_pool / close_pool
delegan correctamente al SimpleConnectionPool. Sin BD real.
"""
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# get_connection
# ---------------------------------------------------------------------------

def test_app_db_get_connection_returns_conn():
    """get_connection() devuelve una conexión desde el pool."""
    import data.app_db as mod

    mock_conn = MagicMock()
    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    orig = mod._pool
    mod._pool = mock_pool
    try:
        result = mod.get_connection()
        assert result is mock_conn
        mock_pool.getconn.assert_called_once()
    finally:
        mod._pool = orig


# ---------------------------------------------------------------------------
# release_connection
# ---------------------------------------------------------------------------

def test_app_db_release_connection_calls_putconn():
    """release_connection(conn) llama a putconn en el pool."""
    import data.app_db as mod

    mock_conn = MagicMock()
    mock_pool = MagicMock()

    orig = mod._pool
    mod._pool = mock_pool
    try:
        mod.release_connection(mock_conn)
        mock_pool.putconn.assert_called_once_with(mock_conn)
    finally:
        mod._pool = orig


def test_app_db_release_noop_when_pool_is_none():
    """release_connection es no-op cuando el pool no fue inicializado."""
    import data.app_db as mod

    mock_conn = MagicMock()
    orig = mod._pool
    mod._pool = None
    try:
        mod.release_connection(mock_conn)  # no debe lanzar
    finally:
        mod._pool = orig


# ---------------------------------------------------------------------------
# init_pool / close_pool
# ---------------------------------------------------------------------------

def test_app_db_init_pool_creates_pool():
    """init_pool() inicializa el pool (llama a SimpleConnectionPool)."""
    import data.app_db as mod

    orig = mod._pool
    mod._pool = None
    try:
        mock_pool = MagicMock()
        with patch("data.app_db.pool.SimpleConnectionPool", return_value=mock_pool):
            mod.init_pool()
        assert mod._pool is mock_pool
    finally:
        mod._pool = orig


def test_app_db_close_pool_closes_all():
    """close_pool() cierra todas las conexiones y resetea el singleton."""
    import data.app_db as mod

    mock_pool = MagicMock()
    orig = mod._pool
    mod._pool = mock_pool
    try:
        mod.close_pool()
        mock_pool.closeall.assert_called_once()
        assert mod._pool is None
    finally:
        mod._pool = orig


def test_app_db_close_pool_noop_when_none():
    """close_pool() no falla cuando el pool ya es None."""
    import data.app_db as mod

    orig = mod._pool
    mod._pool = None
    try:
        mod.close_pool()  # no debe lanzar
    finally:
        mod._pool = orig
