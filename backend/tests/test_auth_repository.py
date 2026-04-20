"""Tests for backend/auth/repository.py — Raw SQL CRUD for auth entities.

TDD — tests written BEFORE implementation.
RED → GREEN cycle: run first to confirm failure, then implement, then confirm pass.

All tests use mock connections (unittest.mock.MagicMock) — no live DB required.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conn_cursor(fetchone_return=None, fetchall_return=None):
    """Build a mock conn + cursor pair.

    Returns (conn, cursor) where cursor is already configured with the
    desired fetchone/fetchall return values.
    """
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone_return
    cursor.fetchall.return_value = fetchall_return if fetchall_return is not None else []

    conn = MagicMock()
    # cursor() called as context manager: with conn.cursor(...) as cur:
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    return conn, cursor


# ---------------------------------------------------------------------------
# get_user_by_username
# ---------------------------------------------------------------------------

class TestGetUserByUsername:
    def test_get_user_by_username_found(self):
        """Returns a dict with user fields + role_name when user exists."""
        from auth.repository import get_user_by_username

        row = {
            "id": 1,
            "username": "john",
            "password_hash": "$2b$12$abc",
            "role_id": 2,
            "is_active": True,
            "role_name": "vendedor",
        }
        conn, cursor = _make_conn_cursor(fetchone_return=row)

        result = get_user_by_username("john", conn=conn)

        assert result is not None
        assert result["username"] == "john"
        assert result["role_name"] == "vendedor"
        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args[0]
        assert "auth.users" in sql
        assert "auth.roles" in sql
        assert params == ("john",)

    def test_get_user_by_username_not_found(self):
        """Returns None when user does not exist."""
        from auth.repository import get_user_by_username

        conn, cursor = _make_conn_cursor(fetchone_return=None)

        result = get_user_by_username("nonexistent", conn=conn)

        assert result is None
        cursor.execute.assert_called_once()


# ---------------------------------------------------------------------------
# get_user_sucursales
# ---------------------------------------------------------------------------

class TestGetUserSucursales:
    def test_get_user_sucursales_returns_list(self):
        """Returns list of int id_sucursal values."""
        from auth.repository import get_user_sucursales

        rows = [{"id_sucursal": 1}, {"id_sucursal": 3}, {"id_sucursal": 5}]
        conn, cursor = _make_conn_cursor(fetchall_return=rows)

        result = get_user_sucursales(42, conn=conn)

        assert result == [1, 3, 5]
        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args[0]
        assert "auth.user_sucursales" in sql
        assert params == (42,)

    def test_get_user_sucursales_empty_returns_empty_list(self):
        """Returns empty list when user has no sucursales assigned."""
        from auth.repository import get_user_sucursales

        conn, cursor = _make_conn_cursor(fetchall_return=[])

        result = get_user_sucursales(99, conn=conn)

        assert result == []
        cursor.execute.assert_called_once()


# ---------------------------------------------------------------------------
# save_refresh_token
# ---------------------------------------------------------------------------

class TestSaveRefreshToken:
    def test_save_refresh_token_executes_insert(self):
        """Executes INSERT into auth.refresh_tokens with correct params."""
        from auth.repository import save_refresh_token

        conn, cursor = _make_conn_cursor()
        expires_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        save_refresh_token(1, "hashed_token_abc", expires_at, conn=conn)

        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args[0]
        assert "auth.refresh_tokens" in sql
        assert "INSERT" in sql.upper()
        assert params == (1, "hashed_token_abc", expires_at)
        conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# get_refresh_token
# ---------------------------------------------------------------------------

class TestGetRefreshToken:
    def test_get_refresh_token_found(self):
        """Returns dict when a valid, non-revoked, non-expired token is found."""
        from auth.repository import get_refresh_token

        row = {
            "id": 10,
            "user_id": 1,
            "token_hash": "hashed_token_abc",
            "expires_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "revoked": False,
        }
        conn, cursor = _make_conn_cursor(fetchone_return=row)

        result = get_refresh_token("hashed_token_abc", conn=conn)

        assert result is not None
        assert result["token_hash"] == "hashed_token_abc"
        assert result["revoked"] is False
        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args[0]
        assert "auth.refresh_tokens" in sql
        assert params == ("hashed_token_abc",)

    def test_get_refresh_token_not_found(self):
        """Returns None when token doesn't exist, is revoked, or is expired."""
        from auth.repository import get_refresh_token

        conn, cursor = _make_conn_cursor(fetchone_return=None)

        result = get_refresh_token("nonexistent_hash", conn=conn)

        assert result is None
        cursor.execute.assert_called_once()


# ---------------------------------------------------------------------------
# revoke_refresh_token
# ---------------------------------------------------------------------------

class TestRevokeRefreshToken:
    def test_revoke_refresh_token_executes_update(self):
        """Executes UPDATE setting revoked=true for the given token_hash."""
        from auth.repository import revoke_refresh_token

        conn, cursor = _make_conn_cursor()

        revoke_refresh_token("hashed_token_abc", conn=conn)

        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args[0]
        assert "auth.refresh_tokens" in sql
        assert "UPDATE" in sql.upper()
        assert "revoked" in sql.lower()
        assert params == ("hashed_token_abc",)
        conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# revoke_all_user_tokens
# ---------------------------------------------------------------------------

class TestRevokeAllUserTokens:
    def test_revoke_all_user_tokens_executes_update(self):
        """Executes UPDATE setting revoked=true for all non-revoked tokens of a user."""
        from auth.repository import revoke_all_user_tokens

        conn, cursor = _make_conn_cursor()

        revoke_all_user_tokens(42, conn=conn)

        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args[0]
        assert "auth.refresh_tokens" in sql
        assert "UPDATE" in sql.upper()
        assert "revoked" in sql.lower()
        assert params == (42,)
        conn.commit.assert_called_once()
