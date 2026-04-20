"""Tests for admin repository functions in backend/auth/repository.py.

TDD — tests written BEFORE implementation.
All tests use mock connections (unittest.mock.MagicMock) — no live DB required.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conn_cursor(fetchone_return=None, fetchall_return=None):
    """Build a mock conn + cursor pair."""
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone_return
    cursor.fetchall.return_value = fetchall_return if fetchall_return is not None else []

    conn = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    return conn, cursor


# ---------------------------------------------------------------------------
# list_users
# ---------------------------------------------------------------------------

class TestListUsers:
    def test_returns_list_of_dicts(self):
        """list_users returns a list of user dicts with role_name."""
        from auth.repository import list_users

        rows = [
            {"id": 1, "username": "admin", "full_name": "Admin", "role_name": "admin", "is_active": True},
            {"id": 2, "username": "juan", "full_name": "Juan Pérez", "role_name": "vendedor", "is_active": True},
        ]
        conn, cursor = _make_conn_cursor(fetchall_return=rows)

        result = list_users(conn=conn)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["username"] == "admin"
        assert result[1]["username"] == "juan"
        cursor.execute.assert_called_once()

    def test_returns_empty_when_no_users(self):
        """list_users returns empty list when no rows."""
        from auth.repository import list_users

        conn, cursor = _make_conn_cursor(fetchall_return=[])
        result = list_users(conn=conn)
        assert result == []

    def test_sql_orders_by_username(self):
        """Query includes ORDER BY username."""
        from auth.repository import list_users

        conn, cursor = _make_conn_cursor(fetchall_return=[])
        list_users(conn=conn)
        sql = cursor.execute.call_args[0][0]
        assert "ORDER BY" in sql.upper()


# ---------------------------------------------------------------------------
# get_user_by_id
# ---------------------------------------------------------------------------

class TestGetUserById:
    def test_returns_dict_when_found(self):
        """get_user_by_id returns a dict with role_name when user exists."""
        from auth.repository import get_user_by_id

        row = {
            "id": 1,
            "username": "admin",
            "password_hash": "$2b$12$abc",
            "full_name": "Admin User",
            "role_id": 1,
            "role_name": "admin",
            "is_active": True,
        }
        conn, cursor = _make_conn_cursor(fetchone_return=row)

        result = get_user_by_id(1, conn=conn)

        assert result is not None
        assert result["id"] == 1
        assert result["username"] == "admin"
        sql, params = cursor.execute.call_args[0]
        assert params == (1,)

    def test_returns_none_when_not_found(self):
        """get_user_by_id returns None when user does not exist."""
        from auth.repository import get_user_by_id

        conn, cursor = _make_conn_cursor(fetchone_return=None)
        result = get_user_by_id(999, conn=conn)
        assert result is None


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

class TestCreateUser:
    def test_returns_new_user_id(self):
        """create_user inserts and returns the new user id."""
        from auth.repository import create_user

        conn, cursor = _make_conn_cursor(fetchone_return={"id": 42})

        result = create_user(
            username="new_user",
            password_hash="$2b$12$xyz",
            full_name="Nuevo Usuario",
            role_id=2,
            conn=conn,
        )

        assert result == 42
        conn.commit.assert_called_once()

    def test_sql_inserts_into_auth_users(self):
        """INSERT targets auth.users."""
        from auth.repository import create_user

        conn, cursor = _make_conn_cursor(fetchone_return={"id": 1})
        create_user("u", "h", "Full Name", 1, conn=conn)

        sql = cursor.execute.call_args[0][0]
        assert "auth.users" in sql.lower()
        assert "INSERT" in sql.upper()

    def test_commits_on_success(self):
        """create_user commits the transaction."""
        from auth.repository import create_user

        conn, cursor = _make_conn_cursor(fetchone_return={"id": 5})
        create_user("u2", "h2", "Name", 3, conn=conn)
        conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# update_user
# ---------------------------------------------------------------------------

class TestUpdateUser:
    def test_updates_user_fields(self):
        """update_user executes UPDATE and commits."""
        from auth.repository import update_user

        conn, cursor = _make_conn_cursor()
        update_user(
            user_id=1,
            full_name="Updated Name",
            role_id=2,
            is_active=False,
            conn=conn,
        )

        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args[0]
        assert "UPDATE" in sql.upper()
        assert "auth.users" in sql.lower()
        conn.commit.assert_called_once()

    def test_params_include_user_id(self):
        """update_user passes user_id as a param."""
        from auth.repository import update_user

        conn, cursor = _make_conn_cursor()
        update_user(1, "Name", 1, True, conn=conn)
        _, params = cursor.execute.call_args[0]
        assert 1 in params


# ---------------------------------------------------------------------------
# set_user_password
# ---------------------------------------------------------------------------

class TestSetUserPassword:
    def test_updates_password_hash(self):
        """set_user_password executes UPDATE and commits."""
        from auth.repository import set_user_password

        conn, cursor = _make_conn_cursor()
        set_user_password(user_id=1, password_hash="$2b$12$new", conn=conn)

        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args[0]
        assert "password_hash" in sql.lower()
        assert "$2b$12$new" in params
        conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# replace_user_sucursales
# ---------------------------------------------------------------------------

class TestReplaceUserSucursales:
    def test_deletes_then_inserts(self):
        """replace_user_sucursales deletes existing rows then inserts new ones."""
        from auth.repository import replace_user_sucursales

        conn, cursor = _make_conn_cursor()
        replace_user_sucursales(user_id=1, sucursal_ids=[10, 20], conn=conn)

        calls = cursor.execute.call_args_list
        # First call: DELETE
        assert len(calls) >= 1
        delete_sql = calls[0][0][0].upper()
        assert "DELETE" in delete_sql
        conn.commit.assert_called_once()

    def test_inserts_each_sucursal(self):
        """replace_user_sucursales inserts one row per sucursal_id."""
        from auth.repository import replace_user_sucursales

        conn, cursor = _make_conn_cursor()
        replace_user_sucursales(user_id=1, sucursal_ids=[10, 20, 30], conn=conn)

        # 1 DELETE + 3 INSERTs = 4 execute calls
        assert cursor.execute.call_count == 4

    def test_empty_sucursales_only_deletes(self):
        """replace_user_sucursales with empty list deletes but inserts nothing."""
        from auth.repository import replace_user_sucursales

        conn, cursor = _make_conn_cursor()
        replace_user_sucursales(user_id=1, sucursal_ids=[], conn=conn)

        # Only DELETE
        assert cursor.execute.call_count == 1
        conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# list_roles
# ---------------------------------------------------------------------------

class TestListRoles:
    def test_returns_list_of_role_dicts(self):
        """list_roles returns all roles as dicts."""
        from auth.repository import list_roles

        rows = [
            {"id": 1, "name": "admin"},
            {"id": 2, "name": "gerente"},
            {"id": 3, "name": "supervisor"},
            {"id": 4, "name": "vendedor"},
        ]
        conn, cursor = _make_conn_cursor(fetchall_return=rows)

        result = list_roles(conn=conn)

        assert len(result) == 4
        assert result[0]["name"] == "admin"
        cursor.execute.assert_called_once()

    def test_sql_queries_auth_roles(self):
        """Query targets auth.roles table."""
        from auth.repository import list_roles

        conn, cursor = _make_conn_cursor(fetchall_return=[])
        list_roles(conn=conn)
        sql = cursor.execute.call_args[0][0]
        assert "auth.roles" in sql.lower()


# ---------------------------------------------------------------------------
# get_role_by_name
# ---------------------------------------------------------------------------

class TestGetRoleByName:
    def test_returns_role_dict_when_found(self):
        """get_role_by_name returns role dict when it exists."""
        from auth.repository import get_role_by_name

        row = {"id": 1, "name": "admin"}
        conn, cursor = _make_conn_cursor(fetchone_return=row)

        result = get_role_by_name("admin", conn=conn)

        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "admin"

    def test_returns_none_when_not_found(self):
        """get_role_by_name returns None for unknown role."""
        from auth.repository import get_role_by_name

        conn, cursor = _make_conn_cursor(fetchone_return=None)
        result = get_role_by_name("unknown", conn=conn)
        assert result is None
