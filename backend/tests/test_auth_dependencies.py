"""Tests for backend/auth/dependencies.py — FastAPI auth dependency functions.

TDD — tests written BEFORE the implementation.
RED → GREEN cycle: run first to confirm failure, then implement, then confirm pass.

All tests mock repository and jwt functions — no live DB or valid JWT required.
"""
import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


def _run(coro):
    """Run an async coroutine in a fresh event loop (Python 3.10+ compatible)."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Helper — build a minimal UserInDB-like dict / object
# ---------------------------------------------------------------------------

def _make_user(role_name: str = "vendedor", is_active: bool = True) -> dict:
    return {
        "id": 1,
        "username": "testuser",
        "password_hash": "$2b$12$xxx",
        "full_name": "Test User",
        "role_id": 2,
        "role_name": role_name,
        "is_active": is_active,
    }


def _import_deps():
    from auth import dependencies as deps
    return deps


# ---------------------------------------------------------------------------
# get_current_user — valid token
# ---------------------------------------------------------------------------

class TestGetCurrentUser:
    def test_get_current_user_valid_token(self, monkeypatch):
        """Valid Bearer token → returns UserInDB with sucursales attached."""
        deps = _import_deps()

        user_dict = _make_user()
        payload = {"sub": "1", "username": "testuser", "role": "vendedor"}

        monkeypatch.setattr("auth.dependencies.decode_token", lambda token: payload)
        monkeypatch.setattr(
            "auth.dependencies.get_user_by_username",
            lambda username, conn=None: user_dict,
        )
        monkeypatch.setattr(
            "auth.dependencies.get_user_sucursales",
            lambda user_id, conn=None: [1, 2],
        )

        result = _run(deps.get_current_user(authorization="Bearer validtoken"))

        assert result.username == "testuser"
        assert result.role_name == "vendedor"
        assert result.sucursales == [1, 2]

    def test_get_current_user_no_header(self):
        """No Authorization header → HTTPException(401, 'Token no proporcionado')."""
        deps = _import_deps()

        with pytest.raises(HTTPException) as exc_info:
            _run(deps.get_current_user(authorization=None))
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token no proporcionado"

    def test_get_current_user_malformed_header(self):
        """Authorization header without 'Bearer' prefix → HTTPException(401)."""
        deps = _import_deps()

        with pytest.raises(HTTPException) as exc_info:
            _run(deps.get_current_user(authorization="Basic sometoken"))
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token no proporcionado"

    def test_get_current_user_invalid_token(self, monkeypatch):
        """decode_token raises HTTPException → dependency re-raises it (401)."""
        deps = _import_deps()

        def _raise(_token):
            raise HTTPException(status_code=401, detail="Token inválido o expirado")

        monkeypatch.setattr("auth.dependencies.decode_token", _raise)

        with pytest.raises(HTTPException) as exc_info:
            _run(deps.get_current_user(authorization="Bearer badtoken"))
        assert exc_info.value.status_code == 401

    def test_get_current_user_user_not_found(self, monkeypatch):
        """get_user_by_username returns None → HTTPException(401, 'Usuario no encontrado')."""
        deps = _import_deps()

        payload = {"sub": "99", "username": "ghost", "role": "vendedor"}
        monkeypatch.setattr("auth.dependencies.decode_token", lambda token: payload)
        monkeypatch.setattr(
            "auth.dependencies.get_user_by_username",
            lambda username, conn=None: None,
        )

        with pytest.raises(HTTPException) as exc_info:
            _run(deps.get_current_user(authorization="Bearer validtoken"))
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Usuario no encontrado"


# ---------------------------------------------------------------------------
# get_current_active_user
# ---------------------------------------------------------------------------

class TestGetCurrentActiveUser:
    def test_get_current_active_user_active(self):
        """Active user passes through unchanged."""
        from auth.models import UserInDB
        deps = _import_deps()

        user = UserInDB(**_make_user(is_active=True))
        user.sucursales = [1]

        result = _run(deps.get_current_active_user(user=user))
        assert result.username == "testuser"
        assert result.is_active is True

    def test_get_current_active_user_inactive(self):
        """Inactive user raises HTTPException(401, 'Usuario inactivo')."""
        from auth.models import UserInDB
        deps = _import_deps()

        user = UserInDB(**_make_user(is_active=False))
        user.sucursales = []

        with pytest.raises(HTTPException) as exc_info:
            _run(deps.get_current_active_user(user=user))
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Usuario inactivo"


# ---------------------------------------------------------------------------
# require_role — factory returning a dependency callable
# ---------------------------------------------------------------------------

class TestRequireRole:
    def _call_dep(self, user, *roles):
        """Helper — invoke the dependency returned by require_role synchronously."""
        deps = _import_deps()
        dep_fn = deps.require_role(*roles)
        return _run(dep_fn(user=user))

    def _make_user_model(self, role_name: str, is_active: bool = True):
        from auth.models import UserInDB
        u = UserInDB(**_make_user(role_name=role_name, is_active=is_active))
        u.sucursales = []
        return u

    def test_require_role_allowed(self):
        """admin in ['admin', 'gerente'] → passes (returns user)."""
        user = self._make_user_model("admin")
        result = self._call_dep(user, "admin", "gerente")
        assert result.username == "testuser"

    def test_require_role_denied(self):
        """vendedor not in ['admin'] → HTTPException(403, 'Permisos insuficientes')."""
        user = self._make_user_model("vendedor")
        with pytest.raises(HTTPException) as exc_info:
            self._call_dep(user, "admin")
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Permisos insuficientes"

    def test_require_role_multiple_roles(self):
        """supervisor in ['admin', 'supervisor'] → passes."""
        user = self._make_user_model("supervisor")
        result = self._call_dep(user, "admin", "supervisor")
        assert result.username == "testuser"
