"""Tests de flujos de autenticación end-to-end (E2E).

Ejercitan flujos completos que abarcan múltiples componentes:
login → refresh → logout, revocación de tokens, RBAC, etc.

Usa la app REAL de main.py con la capa de repositorio mockeada.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt

import config
from auth.dependencies import get_current_active_user, require_role
from auth.jwt import create_access_token, create_refresh_token
from auth.passwords import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(
    username: str = "admin",
    password: str = "secret",
    role_name: str = "admin",
    is_active: bool = True,
    user_id: int = 1,
) -> dict:
    return {
        "id": user_id,
        "username": username,
        "password_hash": hash_password(password),
        "full_name": "Nombre Completo",
        "role_id": 1,
        "role_name": role_name,
        "is_active": is_active,
    }


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# In-memory DB mock
# ---------------------------------------------------------------------------

class InMemoryTokenDB:
    """Base de datos de tokens en memoria para tests."""

    def __init__(self):
        # {token_hash: {"user_id": int, "revoked": bool, "expires_at": datetime}}
        self._tokens: dict[str, dict] = {}

    def save(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        self._tokens[token_hash] = {
            "id": len(self._tokens) + 1,
            "user_id": user_id,
            "token_hash": token_hash,
            "revoked": False,
            "expires_at": expires_at,
        }

    def get(self, token_hash: str) -> dict | None:
        record = self._tokens.get(token_hash)
        if record is None or record["revoked"]:
            return None
        return record

    def revoke(self, token_hash: str) -> None:
        if token_hash in self._tokens:
            self._tokens[token_hash]["revoked"] = True

    def revoke_all(self, user_id: int) -> None:
        for record in self._tokens.values():
            if record["user_id"] == user_id:
                record["revoked"] = True

    def last_saved_hash(self) -> str | None:
        """Devuelve el hash del último token guardado (para inspección en tests)."""
        if not self._tokens:
            return None
        return list(self._tokens.keys())[-1]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def token_db():
    """In-memory token store limpio para cada test."""
    return InMemoryTokenDB()


@pytest.fixture
def mock_user():
    """Usuario admin por defecto."""
    return _make_user()


@pytest.fixture
def real_app_client(monkeypatch, token_db, mock_user):
    """TestClient con la app REAL de main.py y repositorio mockeado."""
    from main import app

    monkeypatch.setattr(
        "auth.router.get_user_by_username",
        lambda u, conn=None: mock_user if u == mock_user["username"] else None,
    )
    monkeypatch.setattr(
        "auth.router.get_user_sucursales",
        lambda uid, conn=None: [1],
    )
    monkeypatch.setattr(
        "auth.router.save_refresh_token",
        lambda user_id, token_hash, expires_at, conn=None: token_db.save(user_id, token_hash, expires_at),
    )
    monkeypatch.setattr(
        "auth.router.get_refresh_token",
        lambda h, conn=None: token_db.get(h),
    )
    monkeypatch.setattr(
        "auth.router.revoke_refresh_token",
        lambda h, conn=None: token_db.revoke(h),
    )
    monkeypatch.setattr(
        "auth.router._get_user_by_id",
        lambda uid: mock_user if uid == mock_user["id"] else None,
    )
    monkeypatch.setattr(
        "auth.dependencies.get_user_by_username",
        lambda u, conn=None: mock_user if u == mock_user["username"] else None,
    )
    monkeypatch.setattr(
        "auth.dependencies.get_user_sucursales",
        lambda uid, conn=None: [1],
    )

    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Test 1: Flujo completo login → refresh → logout
# ---------------------------------------------------------------------------

def test_full_login_refresh_logout_flow(real_app_client):
    """Login → usar access token → refresh → logout → segundo refresh falla."""
    client = real_app_client

    # 1. Login con credenciales válidas
    r_login = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})
    assert r_login.status_code == 200, f"Login falló: {r_login.json()}"
    access_token = r_login.json()["access_token"]
    assert access_token

    # 2. Usar access token en /api/auth/me
    r_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert r_me.status_code == 200, f"/me falló: {r_me.json()}"
    assert r_me.json()["username"] == "admin"

    # 3. Hacer refresh con el cookie (el TestClient lo mantiene automáticamente)
    r_refresh = client.post("/api/auth/refresh")
    assert r_refresh.status_code == 200, f"Refresh falló: {r_refresh.json()}"
    new_access_token = r_refresh.json()["access_token"]
    assert new_access_token
    # El nuevo access token es válido (puede ser igual si la rotación ocurre en el mismo segundo;
    # lo que importa es que el refresh se procesó correctamente y el cookie rotó)
    assert r_refresh.json()["token_type"] == "bearer"

    # 4. Logout limpia el cookie
    r_logout = client.post("/api/auth/logout")
    assert r_logout.status_code == 200
    assert r_logout.json()["message"] == "Sesión cerrada"

    # 5. Intentar refresh con el cookie antiguo (ya revocado) → 401
    r_refresh2 = client.post("/api/auth/refresh")
    assert r_refresh2.status_code == 401


# ---------------------------------------------------------------------------
# Test 2: Token revocado es rechazado
# ---------------------------------------------------------------------------

def test_revoked_token_rejected(real_app_client):
    """Login → logout (revoca token) → intentar refresh → 401."""
    client = real_app_client

    # Login
    r_login = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})
    assert r_login.status_code == 200

    # Logout revoca el refresh token
    r_logout = client.post("/api/auth/logout")
    assert r_logout.status_code == 200

    # Intentar refresh con el token revocado → 401
    r_refresh = client.post("/api/auth/refresh")
    assert r_refresh.status_code == 401


# ---------------------------------------------------------------------------
# Test 3: Hash del refresh token es SHA-256 hex (64 chars)
# ---------------------------------------------------------------------------

def test_refresh_token_hash_is_sha256_hex(real_app_client, token_db):
    """El hash del refresh token guardado en DB es SHA-256 (64 chars hex)."""
    client = real_app_client

    r_login = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})
    assert r_login.status_code == 200

    saved_hash = token_db.last_saved_hash()
    assert saved_hash is not None, "No se guardó ningún token en DB"
    assert len(saved_hash) == 64, f"Hash tiene {len(saved_hash)} chars, esperaba 64"
    assert all(c in "0123456789abcdef" for c in saved_hash), "Hash no es hex válido"


# ---------------------------------------------------------------------------
# Test 4: Endpoints existentes no se rompieron con auth
# ---------------------------------------------------------------------------

def test_existing_endpoints_unchanged_after_auth(real_app_client):
    """Los endpoints de datos siguen respondiendo sin requerir auth.

    /api/sucursales → 200 sin autenticación.
    /api/dashboard → 422 (faltan params requeridos) NO 401, prueba que no está protegido por auth.
    /health → 200 sin autenticación.
    """
    client = real_app_client

    # /api/sucursales sin auth → 200 (no protegido, sin params requeridos)
    r_sucursales = client.get("/api/sucursales")
    assert r_sucursales.status_code == 200, f"/api/sucursales falló: {r_sucursales.status_code}"

    # /api/dashboard sin params → 422 (Unprocessable Entity), NO 401/403 (no protegido por auth)
    r_dashboard = client.get("/api/dashboard")
    assert r_dashboard.status_code == 422, (
        f"Esperaba 422 (params faltantes), obtuve {r_dashboard.status_code} — "
        f"¿el endpoint se protegió con auth por error?"
    )

    # /health sin auth → 200
    r_health = client.get("/health")
    assert r_health.status_code == 200, f"/health falló: {r_health.status_code}"


# ---------------------------------------------------------------------------
# Test 5: require_role bloquea rol no autorizado → 403
# ---------------------------------------------------------------------------

def test_require_role_blocks_unauthorized(monkeypatch):
    """Endpoint con require_role('admin'): vendedor → 403, admin → 200."""
    from auth.router import router as auth_router

    # App mínima con auth router + endpoint de prueba protegido
    _app = FastAPI()
    _app.include_router(auth_router)

    @_app.get("/test/solo-admin")
    async def solo_admin(user=Depends(require_role("admin"))):
        return {"ok": True}

    vendedor_user = _make_user(username="vend", role_name="vendedor", user_id=2)
    admin_user = _make_user(username="admin", role_name="admin", user_id=1)

    def mock_get_user(u, conn=None):
        if u == "vend":
            return vendedor_user
        if u == "admin":
            return admin_user
        return None

    monkeypatch.setattr("auth.dependencies.get_user_by_username", mock_get_user)
    monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: [1])

    client = TestClient(_app, raise_server_exceptions=False)

    # Token de vendedor
    vendedor_token = create_access_token(
        user_id=2,
        username="vend",
        role="vendedor",
        sucursales=[1],
    )
    r_vend = client.get("/test/solo-admin", headers={"Authorization": f"Bearer {vendedor_token}"})
    assert r_vend.status_code == 403, f"Esperaba 403, obtuve {r_vend.status_code}: {r_vend.json()}"

    # Token de admin
    admin_token = create_access_token(
        user_id=1,
        username="admin",
        role="admin",
        sucursales=None,
    )
    r_admin = client.get("/test/solo-admin", headers={"Authorization": f"Bearer {admin_token}"})
    assert r_admin.status_code == 200, f"Esperaba 200, obtuve {r_admin.status_code}: {r_admin.json()}"


# ---------------------------------------------------------------------------
# Test 6: Access token expirado es rechazado en /me
# ---------------------------------------------------------------------------

def test_expired_access_token_rejected_on_me(real_app_client):
    """Token de acceso con exp en el pasado → /api/auth/me devuelve 401."""
    client = real_app_client

    expired_payload = {
        "sub": "1",
        "username": "admin",
        "role": "admin",
        "sucursales": None,
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    expired_token = jwt.encode(expired_payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert r.status_code == 401, f"Esperaba 401, obtuve {r.status_code}: {r.json()}"
