"""Tests for /api/admin/* endpoints in auth/admin_router.py.

TDD — tests written BEFORE the router implementation.
Uses monkeypatch and FastAPI TestClient. No live DB.
All protected endpoints require the admin role.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.passwords import hash_password
from auth.jwt import create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user_db(
    user_id: int = 1,
    username: str = "adminuser",
    role_name: str = "admin",
    is_active: bool = True,
) -> dict:
    return {
        "id": user_id,
        "username": username,
        "password_hash": hash_password("secret"),
        "full_name": "Admin User",
        "role_id": 1,
        "role_name": role_name,
        "is_active": is_active,
    }


def _admin_token(user_id: int = 1, username: str = "adminuser") -> str:
    return create_access_token(
        user_id=user_id,
        username=username,
        role="admin",
        sucursales=None,
    )


def _vendor_token() -> str:
    return create_access_token(
        user_id=99,
        username="vendedor1",
        role="vendedor",
        sucursales=[1],
    )


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def app_with_admin(monkeypatch):
    """FastAPI app with admin_router + auth dependencies mocked."""
    from auth.admin_router import router as admin_router

    _app = FastAPI()
    _app.include_router(admin_router)
    return _app


@pytest.fixture
def client_as_admin(app_with_admin, monkeypatch):
    """TestClient with admin user mocked through auth.dependencies."""
    admin_db = _make_user_db()

    # Patch where auth.dependencies looks them up (imported names)
    monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: admin_db if u == "adminuser" else None)
    monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: [])

    return TestClient(app_with_admin, headers={"Authorization": f"Bearer {_admin_token()}"})


@pytest.fixture
def client_as_vendor(app_with_admin, monkeypatch):
    """TestClient with vendedor user — should get 403 on admin endpoints."""
    vendor_db = _make_user_db(user_id=99, username="vendedor1", role_name="vendedor")

    monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: vendor_db if u == "vendedor1" else None)
    monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: [1])

    return TestClient(app_with_admin, headers={"Authorization": f"Bearer {_vendor_token()}"})


# ---------------------------------------------------------------------------
# RF-GUARD: Non-admin gets 403
# ---------------------------------------------------------------------------

class TestRoleGuard:
    def test_vendor_cannot_list_users(self, client_as_vendor):
        """Vendedor role gets 403 on GET /api/admin/users."""
        res = client_as_vendor.get("/api/admin/users")
        assert res.status_code == 403

    def test_unauthenticated_gets_401(self, app_with_admin):
        """No token → 401."""
        client = TestClient(app_with_admin)
        res = client.get("/api/admin/users")
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# RF-USER-LIST: GET /api/admin/users
# ---------------------------------------------------------------------------

class TestListUsers:
    def test_returns_list(self, client_as_admin, monkeypatch):
        """GET /api/admin/users returns a list of users."""
        rows = [
            {"id": 1, "username": "admin", "full_name": "Admin", "role_name": "admin", "is_active": True},
            {"id": 2, "username": "juan", "full_name": "Juan", "role_name": "vendedor", "is_active": True},
        ]
        monkeypatch.setattr("auth.admin_router.list_users", lambda conn=None: rows)
        monkeypatch.setattr("auth.admin_router.get_user_sucursales", lambda uid, conn=None: [])

        res = client_as_admin.get("/api/admin/users")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["username"] == "admin"

    def test_returns_empty_list_when_no_users(self, client_as_admin, monkeypatch):
        """Returns [] when no users exist."""
        monkeypatch.setattr("auth.admin_router.list_users", lambda conn=None: [])
        res = client_as_admin.get("/api/admin/users")
        assert res.status_code == 200
        assert res.json() == []


# ---------------------------------------------------------------------------
# RF-USER-GET: GET /api/admin/users/{id}
# ---------------------------------------------------------------------------

class TestGetUser:
    def test_returns_user_when_found(self, client_as_admin, monkeypatch):
        """Returns 200 with user data when user exists."""
        user_row = {"id": 2, "username": "juan", "full_name": "Juan", "role_name": "vendedor", "is_active": True}
        monkeypatch.setattr("auth.admin_router.get_user_by_id", lambda uid, conn=None: user_row if uid == 2 else None)
        monkeypatch.setattr("auth.admin_router.get_user_sucursales", lambda uid, conn=None: [10, 20])

        res = client_as_admin.get("/api/admin/users/2")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == 2
        assert data["sucursales"] == [10, 20]

    def test_returns_404_when_not_found(self, client_as_admin, monkeypatch):
        """Returns 404 when user does not exist."""
        monkeypatch.setattr("auth.admin_router.get_user_by_id", lambda uid, conn=None: None)

        res = client_as_admin.get("/api/admin/users/999")
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# RF-USER-CREATE: POST /api/admin/users
# ---------------------------------------------------------------------------

class TestCreateUser:
    def test_creates_user_returns_201(self, client_as_admin, monkeypatch):
        """Valid payload creates user and returns 201 with user data."""
        monkeypatch.setattr("auth.admin_router.get_role_by_name", lambda name, conn=None: {"id": 4, "name": "vendedor"})
        monkeypatch.setattr("auth.admin_router.create_user", lambda **kw: 10)
        monkeypatch.setattr("auth.admin_router.replace_user_sucursales", lambda user_id, sucursal_ids, conn=None: None)
        monkeypatch.setattr(
            "auth.admin_router.get_user_by_id",
            lambda uid, conn=None: {"id": 10, "username": "new_user", "full_name": "New User", "role_name": "vendedor", "is_active": True},
        )
        monkeypatch.setattr("auth.admin_router.get_user_sucursales", lambda uid, conn=None: [1])

        res = client_as_admin.post("/api/admin/users", json={
            "username": "new_user",
            "password": "secret123",
            "full_name": "New User",
            "role": "vendedor",
            "sucursales": [1],
        })
        assert res.status_code == 201
        data = res.json()
        assert data["id"] == 10
        assert data["username"] == "new_user"

    def test_unknown_role_returns_400(self, client_as_admin, monkeypatch):
        """Returns 400 when role does not exist."""
        monkeypatch.setattr("auth.admin_router.get_role_by_name", lambda name, conn=None: None)

        res = client_as_admin.post("/api/admin/users", json={
            "username": "u",
            "password": "secret123",
            "full_name": "F",
            "role": "nonexistent",
        })
        assert res.status_code == 400

    def test_duplicate_username_returns_409(self, client_as_admin, monkeypatch):
        """Returns 409 when username already exists."""
        import psycopg2

        monkeypatch.setattr("auth.admin_router.get_role_by_name", lambda name, conn=None: {"id": 4, "name": "vendedor"})

        def _raise_unique(*args, **kwargs):
            raise psycopg2.errors.UniqueViolation("duplicate key value violates unique constraint")

        monkeypatch.setattr("auth.admin_router.create_user", _raise_unique)

        res = client_as_admin.post("/api/admin/users", json={
            "username": "duplicate",
            "password": "secret123",
            "full_name": "F",
            "role": "vendedor",
        })
        assert res.status_code == 409


# ---------------------------------------------------------------------------
# RF-USER-UPDATE: PATCH /api/admin/users/{id}
# ---------------------------------------------------------------------------

class TestUpdateUser:
    def test_updates_user(self, client_as_admin, monkeypatch):
        """Valid PATCH updates user and returns 200."""
        existing = {"id": 2, "username": "juan", "full_name": "Juan", "role_name": "vendedor", "role_id": 4, "is_active": True}
        monkeypatch.setattr("auth.admin_router.get_user_by_id", lambda uid, conn=None: existing if uid == 2 else None)
        monkeypatch.setattr("auth.admin_router.get_role_by_name", lambda name, conn=None: {"id": 3, "name": "supervisor"})
        monkeypatch.setattr("auth.admin_router.update_user", lambda **kw: None)
        monkeypatch.setattr("auth.admin_router.replace_user_sucursales", lambda user_id, sucursal_ids, conn=None: None)
        monkeypatch.setattr("auth.admin_router.get_user_sucursales", lambda uid, conn=None: [5])

        res = client_as_admin.patch("/api/admin/users/2", json={"role": "supervisor"})
        assert res.status_code == 200

    def test_returns_404_when_not_found(self, client_as_admin, monkeypatch):
        """Returns 404 when user does not exist."""
        monkeypatch.setattr("auth.admin_router.get_user_by_id", lambda uid, conn=None: None)
        res = client_as_admin.patch("/api/admin/users/999", json={"is_active": False})
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# RF-SELF-PROTECT
# ---------------------------------------------------------------------------

class TestSelfProtect:
    def test_admin_cannot_deactivate_self(self, client_as_admin, monkeypatch):
        """Admin deactivating own account returns 400."""
        own_user = _make_user_db()  # id=1, role=admin
        monkeypatch.setattr("auth.admin_router.get_user_by_id", lambda uid, conn=None: own_user if uid == 1 else None)

        res = client_as_admin.patch("/api/admin/users/1", json={"is_active": False})
        assert res.status_code == 400
        assert "propio" in res.json()["detail"].lower() or "self" in res.json()["detail"].lower() or "propia" in res.json()["detail"].lower()

    def test_admin_cannot_demote_self(self, client_as_admin, monkeypatch):
        """Admin changing own role returns 400."""
        own_user = _make_user_db()  # id=1, role=admin
        monkeypatch.setattr("auth.admin_router.get_user_by_id", lambda uid, conn=None: own_user if uid == 1 else None)
        monkeypatch.setattr("auth.admin_router.get_role_by_name", lambda name, conn=None: {"id": 4, "name": "vendedor"})

        res = client_as_admin.patch("/api/admin/users/1", json={"role": "vendedor"})
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# RF-USER-RESET-PW: POST /api/admin/users/{id}/password
# ---------------------------------------------------------------------------

class TestResetPassword:
    def test_resets_password(self, client_as_admin, monkeypatch):
        """Admin can reset another user's password."""
        target = {"id": 2, "username": "juan", "full_name": "Juan", "role_id": 4, "role_name": "vendedor", "is_active": True}
        monkeypatch.setattr("auth.admin_router.get_user_by_id", lambda uid, conn=None: target if uid == 2 else None)
        monkeypatch.setattr("auth.admin_router.set_user_password", lambda user_id, password_hash, conn=None: None)

        res = client_as_admin.post("/api/admin/users/2/password", json={"password": "newpassword"})
        assert res.status_code == 200

    def test_returns_404_for_unknown_user(self, client_as_admin, monkeypatch):
        """Returns 404 when target user doesn't exist."""
        monkeypatch.setattr("auth.admin_router.get_user_by_id", lambda uid, conn=None: None)
        res = client_as_admin.post("/api/admin/users/999/password", json={"password": "newpassword"})
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# RF-ROLES-LIST: GET /api/admin/roles
# ---------------------------------------------------------------------------

class TestListRoles:
    def test_returns_roles(self, client_as_admin, monkeypatch):
        """Returns list of all roles."""
        roles = [{"id": 1, "name": "admin"}, {"id": 2, "name": "gerente"}]
        monkeypatch.setattr("auth.admin_router.list_roles", lambda conn=None: roles)

        res = client_as_admin.get("/api/admin/roles")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2
        assert data[0]["name"] == "admin"


# ---------------------------------------------------------------------------
# RF-SUCURSALES-LIST: GET /api/admin/sucursales
# ---------------------------------------------------------------------------

class TestListSucursales:
    def test_returns_sucursales(self, client_as_admin, monkeypatch):
        """Returns list of sucursales."""
        suc = [{"id": 1, "descripcion": "Sucursal Norte"}, {"id": 2, "descripcion": "Sucursal Sur"}]
        monkeypatch.setattr("auth.admin_router.list_sucursales_db", lambda conn=None: suc)

        res = client_as_admin.get("/api/admin/sucursales")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
