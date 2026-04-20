"""Tests for backend/data/auth_db.py

Verifies that get_auth_connection and release_auth_connection delegate
correctly to the SimpleConnectionPool — no live DB required.
"""
from unittest.mock import MagicMock, patch


def test_auth_db_get_connection_returns_conn():
    """get_auth_connection() returns a connection from the pool."""
    import data.auth_db as auth_db_module

    mock_conn = MagicMock()
    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    # Reset singleton so the mock pool is used
    original_pool = auth_db_module._auth_pool
    auth_db_module._auth_pool = mock_pool
    try:
        result = auth_db_module.get_auth_connection()
        assert result is mock_conn
        mock_pool.getconn.assert_called_once()
    finally:
        auth_db_module._auth_pool = original_pool


def test_auth_db_release_connection_calls_putconn():
    """release_auth_connection(conn) calls putconn on the pool."""
    import data.auth_db as auth_db_module

    mock_conn = MagicMock()
    mock_pool = MagicMock()

    original_pool = auth_db_module._auth_pool
    auth_db_module._auth_pool = mock_pool
    try:
        auth_db_module.release_auth_connection(mock_conn)
        mock_pool.putconn.assert_called_once_with(mock_conn)
    finally:
        auth_db_module._auth_pool = original_pool


def test_auth_db_release_noop_when_pool_is_none():
    """release_auth_connection is a no-op when pool has not been initialized."""
    import data.auth_db as auth_db_module

    mock_conn = MagicMock()
    original_pool = auth_db_module._auth_pool
    auth_db_module._auth_pool = None
    try:
        # Should not raise
        auth_db_module.release_auth_connection(mock_conn)
    finally:
        auth_db_module._auth_pool = original_pool
