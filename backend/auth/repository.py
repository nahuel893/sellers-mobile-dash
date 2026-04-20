"""Raw SQL CRUD for auth entities.

All functions accept an optional ``conn`` parameter. When omitted, a connection
is borrowed from the pool and released automatically (own_conn pattern).

Uses psycopg2.extras.RealDictCursor so fetchone/fetchall return dict-like rows.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import psycopg2.extras

from data.auth_db import get_auth_connection as get_connection, release_auth_connection as release_connection


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cursor(conn):
    """Return a RealDictCursor context manager for the given connection."""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def get_user_by_username(username: str, conn=None) -> dict | None:
    """Fetch a user row joined with its role name.

    Returns a dict with all ``auth.users`` columns plus ``role_name``,
    or ``None`` if not found.
    """
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = """
            SELECT u.*, r.name AS role_name
            FROM auth.users u
            JOIN auth.roles r ON u.role_id = r.id
            WHERE u.username = %s
        """
        with _cursor(conn) as cur:
            cur.execute(sql, (username,))
            row = cur.fetchone()
            return dict(row) if row is not None else None
    finally:
        if own_conn:
            release_connection(conn)


def get_user_sucursales(user_id: int, conn=None) -> list[int]:
    """Return the list of ``id_sucursal`` values assigned to *user_id*.

    Returns an empty list when the user has no sucursales.
    """
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = "SELECT id_sucursal FROM auth.user_sucursales WHERE user_id = %s"
        with _cursor(conn) as cur:
            cur.execute(sql, (user_id,))
            rows = cur.fetchall()
            return [row["id_sucursal"] for row in rows]
    finally:
        if own_conn:
            release_connection(conn)


# ---------------------------------------------------------------------------
# Refresh tokens
# ---------------------------------------------------------------------------

def save_refresh_token(
    user_id: int,
    token_hash: str,
    expires_at: datetime,
    conn=None,
) -> None:
    """Persist a new refresh token record."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = """
            INSERT INTO auth.refresh_tokens (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s)
        """
        with _cursor(conn) as cur:
            cur.execute(sql, (user_id, token_hash, expires_at))
        conn.commit()
    finally:
        if own_conn:
            release_connection(conn)


def get_refresh_token(token_hash: str, conn=None) -> dict | None:
    """Look up a valid (non-revoked, non-expired) refresh token.

    Returns a dict or ``None`` if the token is invalid/missing.
    """
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = """
            SELECT *
            FROM auth.refresh_tokens
            WHERE token_hash = %s
              AND revoked = false
              AND expires_at > NOW()
        """
        with _cursor(conn) as cur:
            cur.execute(sql, (token_hash,))
            row = cur.fetchone()
            return dict(row) if row is not None else None
    finally:
        if own_conn:
            release_connection(conn)


def get_refresh_token_any(token_hash: str, conn=None) -> dict | None:
    """Look up a refresh token record WITHOUT filtering by revoked/expiry.

    Use to detect reuse of a revoked token (security escalation).
    Returns a dict or ``None`` if the hash has never been stored.
    """
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = "SELECT * FROM auth.refresh_tokens WHERE token_hash = %s"
        with _cursor(conn) as cur:
            cur.execute(sql, (token_hash,))
            row = cur.fetchone()
            return dict(row) if row is not None else None
    finally:
        if own_conn:
            release_connection(conn)


def revoke_refresh_token(token_hash: str, conn=None) -> None:
    """Mark a single refresh token as revoked."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = "UPDATE auth.refresh_tokens SET revoked = true WHERE token_hash = %s"
        with _cursor(conn) as cur:
            cur.execute(sql, (token_hash,))
        conn.commit()
    finally:
        if own_conn:
            release_connection(conn)


def revoke_all_user_tokens(user_id: int, conn=None) -> None:
    """Revoke all active refresh tokens belonging to *user_id*."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = """
            UPDATE auth.refresh_tokens
            SET revoked = true
            WHERE user_id = %s AND revoked = false
        """
        with _cursor(conn) as cur:
            cur.execute(sql, (user_id,))
        conn.commit()
    finally:
        if own_conn:
            release_connection(conn)


# ---------------------------------------------------------------------------
# Admin CRUD — Users
# ---------------------------------------------------------------------------

def list_users(conn=None) -> list[dict]:
    """Return all users joined with their role name, ordered by username."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = """
            SELECT u.id, u.username, u.full_name, u.is_active,
                   u.role_id, r.name AS role_name,
                   u.created_at
            FROM auth.users u
            JOIN auth.roles r ON u.role_id = r.id
            ORDER BY u.username
        """
        with _cursor(conn) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        if own_conn:
            release_connection(conn)


def get_user_by_id(user_id: int, conn=None) -> dict | None:
    """Fetch a single user row joined with its role name, or None if not found."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = """
            SELECT u.*, r.name AS role_name
            FROM auth.users u
            JOIN auth.roles r ON u.role_id = r.id
            WHERE u.id = %s
        """
        with _cursor(conn) as cur:
            cur.execute(sql, (user_id,))
            row = cur.fetchone()
            return dict(row) if row is not None else None
    finally:
        if own_conn:
            release_connection(conn)


def create_user(
    username: str,
    password_hash: str,
    full_name: str,
    role_id: int,
    conn=None,
) -> int:
    """Insert a new user and return its generated id.

    Raises psycopg2.errors.UniqueViolation when username already exists
    (caller should catch and convert to HTTP 409).
    """
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = """
            INSERT INTO auth.users (username, password_hash, full_name, role_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        with _cursor(conn) as cur:
            cur.execute(sql, (username, password_hash, full_name, role_id))
            row = cur.fetchone()
        conn.commit()
        return row["id"]
    finally:
        if own_conn:
            release_connection(conn)


def update_user(
    user_id: int,
    full_name: str,
    role_id: int,
    is_active: bool,
    conn=None,
) -> None:
    """Update user's full_name, role_id, and is_active."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = """
            UPDATE auth.users
            SET full_name = %s, role_id = %s, is_active = %s
            WHERE id = %s
        """
        with _cursor(conn) as cur:
            cur.execute(sql, (full_name, role_id, is_active, user_id))
        conn.commit()
    finally:
        if own_conn:
            release_connection(conn)


def set_user_password(user_id: int, password_hash: str, conn=None) -> None:
    """Replace the stored password hash for a user."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = "UPDATE auth.users SET password_hash = %s WHERE id = %s"
        with _cursor(conn) as cur:
            cur.execute(sql, (password_hash, user_id))
        conn.commit()
    finally:
        if own_conn:
            release_connection(conn)


def replace_user_sucursales(user_id: int, sucursal_ids: list[int], conn=None) -> None:
    """Replace all sucursal assignments for a user (delete-then-insert).

    This is an atomic replace: all previous assignments are deleted and the
    provided list is inserted in their place.
    """
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        with _cursor(conn) as cur:
            cur.execute(
                "DELETE FROM auth.user_sucursales WHERE user_id = %s",
                (user_id,),
            )
            for sid in sucursal_ids:
                cur.execute(
                    "INSERT INTO auth.user_sucursales (user_id, id_sucursal) VALUES (%s, %s)",
                    (user_id, sid),
                )
        conn.commit()
    finally:
        if own_conn:
            release_connection(conn)


# ---------------------------------------------------------------------------
# Admin CRUD — Roles
# ---------------------------------------------------------------------------

def list_roles(conn=None) -> list[dict]:
    """Return all roles from auth.roles."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = "SELECT id, name FROM auth.roles ORDER BY id"
        with _cursor(conn) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        if own_conn:
            release_connection(conn)


def get_role_by_name(name: str, conn=None) -> dict | None:
    """Return a role dict by name, or None if not found."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        sql = "SELECT id, name FROM auth.roles WHERE name = %s"
        with _cursor(conn) as cur:
            cur.execute(sql, (name,))
            row = cur.fetchone()
            return dict(row) if row is not None else None
    finally:
        if own_conn:
            release_connection(conn)
