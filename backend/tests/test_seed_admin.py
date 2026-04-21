"""Tests for backend/scripts/seed_admin.py

All tests mock the DB connection — no real PostgreSQL required.
Uses monkeypatch for env vars and unittest.mock for psycopg2.
"""
import sys
import importlib
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_seed():
    """Force-reload the module so env vars are re-read each test."""
    mod_name = "scripts.seed_admin"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    return importlib.import_module(mod_name)


def _make_cursor_mock(fetchone_return=None):
    """Build a mock cursor that supports the context-manager protocol."""
    cur = MagicMock()
    cur.fetchone.return_value = fetchone_return
    # Support `with conn.cursor() as cur:` pattern
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=cur)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx, cur


def _make_conn_mock(fetchone_return=None):
    """Build a psycopg2 connection mock with a cursor mock attached."""
    ctx, cur = _make_cursor_mock(fetchone_return=fetchone_return)
    conn = MagicMock()
    conn.cursor.return_value = ctx
    return conn, cur


# ---------------------------------------------------------------------------
# Test: requires ADMIN_PASSWORD
# ---------------------------------------------------------------------------

def test_seed_requires_admin_password(monkeypatch):
    """Script must fail when ADMIN_PASSWORD is not set."""
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    # Prevent the module from re-populating ADMIN_PASSWORD from the real
    # .env file during reload.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: None)

    with patch("scripts.seed_admin.psycopg2.connect") as mock_connect:
        mock_connect.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)

        seed = _reload_seed()
        # Re-delete after reload, in case load_dotenv was already called with
        # the patched version but ADMIN_PASSWORD leaked from another test fixture.
        monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
        import pytest
        with pytest.raises((SystemExit, ValueError)):
            seed.seed_admin()


# ---------------------------------------------------------------------------
# Test: password is hashed with bcrypt
# ---------------------------------------------------------------------------

def test_seed_password_is_hashed(monkeypatch):
    """The value stored in the DB must be a bcrypt hash, not plain text."""
    monkeypatch.setenv("ADMIN_PASSWORD", "supersecret")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_FULL_NAME", "Administrador")

    conn, cur = _make_conn_mock(fetchone_return={"id": 1})  # role found

    stored_hash = None

    def capture_execute(sql, params=None):
        nonlocal stored_hash
        if params and "supersecret" not in str(params):
            # This is the upsert — capture the hash
            if isinstance(params, (list, tuple)) and len(params) >= 2:
                # password_hash is second param in INSERT
                candidate = params[1] if len(params) > 1 else None
                if candidate and isinstance(candidate, str) and candidate.startswith("$2"):
                    stored_hash = candidate

    cur.execute.side_effect = capture_execute

    seed = _reload_seed()

    with patch("scripts.seed_admin.psycopg2.connect", return_value=conn):
        seed.seed_admin()

    assert stored_hash is not None, "No bcrypt hash was captured from execute calls"
    assert stored_hash.startswith("$2b$"), f"Expected bcrypt hash starting with $2b$, got: {stored_hash!r}"


# ---------------------------------------------------------------------------
# Test: role_id lookup
# ---------------------------------------------------------------------------

def test_seed_uses_admin_role_id(monkeypatch):
    """Script must query auth.roles to find the 'admin' role id."""
    monkeypatch.setenv("ADMIN_PASSWORD", "pass123")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")

    conn, cur = _make_conn_mock()

    # First fetchone → role lookup returns {"id": 42}
    # Second fetchone → user upsert (no result needed)
    cur.fetchone.side_effect = [{"id": 42}, None]

    executed_sqls = []

    def capture_execute(sql, params=None):
        executed_sqls.append((sql.strip(), params))

    cur.execute.side_effect = capture_execute

    seed = _reload_seed()

    with patch("scripts.seed_admin.psycopg2.connect", return_value=conn):
        seed.seed_admin()

    # Verify role lookup SQL was executed
    role_queries = [
        (sql, params)
        for sql, params in executed_sqls
        if "auth.roles" in sql and "admin" in str(params or "")
    ]
    assert role_queries, (
        f"Expected a query on auth.roles with 'admin' param. "
        f"Got executed SQLs: {[s for s, _ in executed_sqls]}"
    )


# ---------------------------------------------------------------------------
# Test: INSERT (new user)
# ---------------------------------------------------------------------------

def test_seed_creates_admin_user(monkeypatch):
    """When user does not exist, an INSERT (upsert) must be executed."""
    monkeypatch.setenv("ADMIN_PASSWORD", "mypassword")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_FULL_NAME", "Administrador")

    conn, cur = _make_conn_mock()

    # role fetchone → returns role row; no second fetchone needed for upsert
    cur.fetchone.return_value = {"id": 1}

    executed_sqls = []

    def capture_execute(sql, params=None):
        executed_sqls.append((sql.strip(), params))

    cur.execute.side_effect = capture_execute

    seed = _reload_seed()

    with patch("scripts.seed_admin.psycopg2.connect", return_value=conn):
        seed.seed_admin()

    upsert_sqls = [
        (sql, params)
        for sql, params in executed_sqls
        if "INSERT" in sql.upper() and "auth.users" in sql
    ]
    assert upsert_sqls, (
        f"Expected INSERT INTO auth.users. "
        f"Executed: {[s for s, _ in executed_sqls]}"
    )

    # Verify ON CONFLICT clause for idempotency
    upsert_sql = upsert_sqls[0][0]
    assert "ON CONFLICT" in upsert_sql.upper(), (
        "INSERT must use ON CONFLICT for idempotency"
    )

    # Verify commit was called
    conn.commit.assert_called()


# ---------------------------------------------------------------------------
# Test: UPDATE existing user (idempotency via ON CONFLICT DO UPDATE)
# ---------------------------------------------------------------------------

def test_seed_updates_existing_user(monkeypatch):
    """Running the script twice must update the password (idempotent upsert)."""
    monkeypatch.setenv("ADMIN_PASSWORD", "newpassword")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")

    conn, cur = _make_conn_mock()
    cur.fetchone.return_value = {"id": 1}

    executed_sqls = []

    def capture_execute(sql, params=None):
        executed_sqls.append((sql.strip(), params))

    cur.execute.side_effect = capture_execute

    seed = _reload_seed()

    # Run twice — both must succeed without errors
    with patch("scripts.seed_admin.psycopg2.connect", return_value=conn):
        seed.seed_admin()
        seed.seed_admin()

    upsert_sqls = [
        sql for sql, _ in executed_sqls
        if "INSERT" in sql.upper() and "auth.users" in sql
    ]
    # Both runs must have attempted the upsert
    assert len(upsert_sqls) >= 2, (
        f"Expected at least 2 upsert calls (one per run). Got: {upsert_sqls}"
    )

    # Verify the DO UPDATE clause is present
    assert all("DO UPDATE" in sql.upper() for sql in upsert_sqls), (
        "All upsert SQLs must contain DO UPDATE"
    )
