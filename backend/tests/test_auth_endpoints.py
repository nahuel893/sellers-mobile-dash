"""Tests para los endpoints de autenticación /api/auth/*.

TDD: estos tests se escriben ANTES de implementar auth/router.py.

Usa monkeypatch para sustituir las funciones de repositorio — no hay DB en tests.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.passwords import hash_password
from auth.jwt import create_access_token, create_refresh_token


# ---------------------------------------------------------------------------
# Helpers de test
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
# App fixture con auth router montado
# ---------------------------------------------------------------------------

@pytest.fixture
def app_with_auth():
    """Crea una app FastAPI mínima con el auth router, sin lifespan."""
    from auth.router import router as auth_router

    _app = FastAPI()
    _app.include_router(auth_router)
    return _app


@pytest.fixture
def client(app_with_auth):
    return TestClient(app_with_auth, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------

def test_login_success(client, monkeypatch):
    """Login exitoso devuelve access_token y setea cookie httpOnly."""
    user = _make_user()
    monkeypatch.setattr("auth.router.get_user_by_username", lambda u, conn=None: user if u == "admin" else None)
    monkeypatch.setattr("auth.router.get_user_sucursales", lambda uid, conn=None: [])
    monkeypatch.setattr("auth.router.save_refresh_token", lambda *a, **kw: None)

    r = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})

    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    # RF-API-002: respuesta incluye user object con datos públicos
    assert "user" in body and body["user"] is not None
    assert body["user"]["username"] == "admin"
    assert body["user"]["role"] == "admin"
    assert body["user"]["sucursales"] is None  # admin → None (acceso irrestricto)
    # Cookie debe estar presente
    assert "refresh_token" in r.cookies


def test_login_access_token_contains_iat(client, monkeypatch):
    """RF-AUTH-006: el access token debe incluir la claim iat (issued-at)."""
    from jose import jwt as jose_jwt
    import config as cfg

    user = _make_user()
    monkeypatch.setattr("auth.router.get_user_by_username", lambda u, conn=None: user if u == "admin" else None)
    monkeypatch.setattr("auth.router.get_user_sucursales", lambda uid, conn=None: [])
    monkeypatch.setattr("auth.router.save_refresh_token", lambda *a, **kw: None)

    r = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})
    token = r.json()["access_token"]
    payload = jose_jwt.decode(token, cfg.JWT_SECRET_KEY, algorithms=[cfg.JWT_ALGORITHM])
    assert "iat" in payload and isinstance(payload["iat"], int)


def test_login_inactive_user_checked_before_password(client, monkeypatch):
    """RF-AUTH-002: is_active se valida ANTES de verify_password.
    Si el usuario está inactivo, verify_password NO debe ser llamado."""
    user = _make_user(is_active=False)
    monkeypatch.setattr("auth.router.get_user_by_username", lambda u, conn=None: user if u == "admin" else None)

    verify_called: list[bool] = []

    def _fake_verify(*args, **kwargs):
        verify_called.append(True)
        return True

    monkeypatch.setattr("auth.router.verify_password", _fake_verify)

    r = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})

    assert r.status_code == 401
    assert "inactivo" in r.json()["detail"].lower()
    assert verify_called == []  # verify_password NUNCA fue invocado


def test_login_wrong_password(client, monkeypatch):
    """Contraseña incorrecta → 401 con mensaje genérico."""
    user = _make_user()
    monkeypatch.setattr("auth.router.get_user_by_username", lambda u, conn=None: user if u == "admin" else None)
    monkeypatch.setattr("auth.router.get_user_sucursales", lambda uid, conn=None: [])

    r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})

    assert r.status_code == 401
    assert r.json()["detail"] == "Credenciales inválidas"


def test_login_unknown_user(client, monkeypatch):
    """Usuario inexistente → 401 con el MISMO mensaje que contraseña incorrecta."""
    monkeypatch.setattr("auth.router.get_user_by_username", lambda u, conn=None: None)
    monkeypatch.setattr("auth.router.dummy_verify", lambda: None)

    r = client.post("/api/auth/login", json={"username": "nobody", "password": "whatever"})

    assert r.status_code == 401
    assert r.json()["detail"] == "Credenciales inválidas"


def test_login_inactive_user(client, monkeypatch):
    """Usuario inactivo → 401 'Usuario inactivo'."""
    user = _make_user(is_active=False)
    monkeypatch.setattr("auth.router.get_user_by_username", lambda u, conn=None: user)
    monkeypatch.setattr("auth.router.get_user_sucursales", lambda uid, conn=None: [])

    r = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})

    assert r.status_code == 401
    assert r.json()["detail"] == "Usuario inactivo"


def test_login_supervisor_no_branches(client, monkeypatch):
    """Supervisor sin sucursales asignadas → 403."""
    user = _make_user(role_name="supervisor")
    monkeypatch.setattr("auth.router.get_user_by_username", lambda u, conn=None: user)
    monkeypatch.setattr("auth.router.get_user_sucursales", lambda uid, conn=None: [])

    r = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})

    assert r.status_code == 403
    assert "sucursales" in r.json()["detail"].lower()


def test_login_vendedor_no_branches(client, monkeypatch):
    """Vendedor sin sucursales asignadas → 403."""
    user = _make_user(role_name="vendedor")
    monkeypatch.setattr("auth.router.get_user_by_username", lambda u, conn=None: user)
    monkeypatch.setattr("auth.router.get_user_sucursales", lambda uid, conn=None: [])

    r = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})

    assert r.status_code == 403


def test_login_admin_no_branches_ok(client, monkeypatch):
    """Admin sin sucursales asignadas en tabla → login igual exitoso (no restringido)."""
    user = _make_user(role_name="admin")
    monkeypatch.setattr("auth.router.get_user_by_username", lambda u, conn=None: user)
    monkeypatch.setattr("auth.router.get_user_sucursales", lambda uid, conn=None: [])
    monkeypatch.setattr("auth.router.save_refresh_token", lambda *a, **kw: None)

    r = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})

    assert r.status_code == 200


def test_login_cookie_is_httponly(client, monkeypatch):
    """El cookie de refresh_token debe ser httpOnly."""
    user = _make_user()
    monkeypatch.setattr("auth.router.get_user_by_username", lambda u, conn=None: user)
    monkeypatch.setattr("auth.router.get_user_sucursales", lambda uid, conn=None: [])
    monkeypatch.setattr("auth.router.save_refresh_token", lambda *a, **kw: None)

    r = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})

    assert r.status_code == 200
    # TestClient de httpx expone Set-Cookie en headers
    set_cookie = r.headers.get("set-cookie", "")
    assert "httponly" in set_cookie.lower()


def test_login_cookie_path_scoped(client, monkeypatch):
    """El cookie debe tener path=/api/auth (scoped)."""
    user = _make_user()
    monkeypatch.setattr("auth.router.get_user_by_username", lambda u, conn=None: user)
    monkeypatch.setattr("auth.router.get_user_sucursales", lambda uid, conn=None: [])
    monkeypatch.setattr("auth.router.save_refresh_token", lambda *a, **kw: None)

    r = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})

    set_cookie = r.headers.get("set-cookie", "")
    assert "path=/api/auth" in set_cookie.lower()


# ---------------------------------------------------------------------------
# Refresh tests
# ---------------------------------------------------------------------------

def test_refresh_success(client, monkeypatch):
    """Refresh exitoso devuelve nuevo access_token y rota el cookie."""
    # Crear un refresh token real para el test
    refresh_token = create_refresh_token(user_id=1)
    token_hash = _token_hash(refresh_token)

    db_token = {
        "id": 1,
        "user_id": 1,
        "token_hash": token_hash,
        "revoked": False,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
    }
    user = _make_user()

    monkeypatch.setattr("auth.router.get_refresh_token", lambda h, conn=None: db_token if h == token_hash else None)
    monkeypatch.setattr("auth.router.revoke_refresh_token", lambda h, conn=None: None)
    monkeypatch.setattr("auth.router.get_user_sucursales", lambda uid, conn=None: [1])
    monkeypatch.setattr("auth.router.save_refresh_token", lambda *a, **kw: None)
    # _get_user_by_id es función interna del router; la mockeamos en el módulo
    monkeypatch.setattr("auth.router._get_user_by_id", lambda uid: user if uid == 1 else None)

    # Hacer la petición con el cookie seteado
    client.cookies.set("refresh_token", refresh_token)
    r = client.post("/api/auth/refresh")

    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    # Nuevo cookie debe estar en la respuesta
    assert "refresh_token" in r.cookies or "set-cookie" in r.headers


def test_refresh_missing_cookie(client, monkeypatch):
    """Sin cookie → 401."""
    # Asegurar que no hay cookie
    client.cookies.clear()
    r = client.post("/api/auth/refresh")

    assert r.status_code == 401
    assert "refresco" in r.json()["detail"].lower()


def test_refresh_revoked_token(client, monkeypatch):
    """Token revocado (not found in DB) → 401."""
    refresh_token = create_refresh_token(user_id=1)

    # get_refresh_token devuelve None → token inválido/revocado
    monkeypatch.setattr("auth.router.get_refresh_token", lambda h, conn=None: None)
    # get_refresh_token_any retorna None → no hay registro previo, sin escalado
    monkeypatch.setattr("auth.router.get_refresh_token_any", lambda h, conn=None: None)

    client.cookies.set("refresh_token", refresh_token)
    r = client.post("/api/auth/refresh")

    assert r.status_code == 401


def test_refresh_reused_revoked_token_triggers_revoke_all(client, monkeypatch):
    """RF-SEC-009: si el token presentado existe pero está revocado, se deben
    revocar TODOS los tokens activos del usuario (reuse attack detection)."""
    refresh_token = create_refresh_token(user_id=42)

    monkeypatch.setattr("auth.router.get_refresh_token", lambda h, conn=None: None)
    monkeypatch.setattr(
        "auth.router.get_refresh_token_any",
        lambda h, conn=None: {"user_id": 42, "revoked": True},
    )

    revoked_users: list[int] = []
    monkeypatch.setattr(
        "auth.router.revoke_all_user_tokens",
        lambda user_id, conn=None: revoked_users.append(user_id),
    )

    client.cookies.set("refresh_token", refresh_token)
    r = client.post("/api/auth/refresh")

    assert r.status_code == 401
    assert revoked_users == [42]


def test_refresh_expired_token(client, monkeypatch):
    """Token JWT expirado → 401 (decode_token lanza HTTPException)."""
    # Crear un token con expiración en el pasado usando jose directamente
    from datetime import datetime, timezone, timedelta
    from jose import jwt
    import config

    expired_payload = {
        "sub": "1",
        "type": "refresh",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    expired_token = jwt.encode(expired_payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    client.cookies.set("refresh_token", expired_token)
    r = client.post("/api/auth/refresh")

    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Logout tests
# ---------------------------------------------------------------------------

def test_logout_with_cookie(client, monkeypatch):
    """Logout con cookie válido → 200 y limpia cookie."""
    refresh_token = create_refresh_token(user_id=1)
    monkeypatch.setattr("auth.router.revoke_refresh_token", lambda h, conn=None: None)

    client.cookies.set("refresh_token", refresh_token)
    r = client.post("/api/auth/logout")

    assert r.status_code == 200
    assert r.json()["message"] == "Sesión cerrada"
    # Cookie debe ser limpiado (max_age=0 o expires en el pasado)
    set_cookie = r.headers.get("set-cookie", "")
    assert "refresh_token" in set_cookie


def test_logout_without_cookie(client, monkeypatch):
    """Logout sin cookie → igual 200 (idempotente)."""
    client.cookies.clear()
    r = client.post("/api/auth/logout")

    assert r.status_code == 200
    assert r.json()["message"] == "Sesión cerrada"


# ---------------------------------------------------------------------------
# Me tests
# ---------------------------------------------------------------------------

def test_me_valid_token(client, monkeypatch):
    """GET /me con token válido → devuelve datos del usuario."""
    user = _make_user()
    access_token = create_access_token(
        user_id=1,
        username="admin",
        role="admin",
        sucursales=None,
    )

    # get_current_user en dependencies.py usa imports directos; parchamos esos
    monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: user if u == "admin" else None)
    monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: [])

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})

    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "admin"
    assert "password_hash" not in body
    assert "role" in body


def test_me_expired_token(client, monkeypatch):
    """Token expirado → 401."""
    from jose import jwt
    import config

    expired_payload = {
        "sub": "1",
        "username": "admin",
        "role": "admin",
        "sucursales": None,
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    expired_token = jwt.encode(expired_payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

    assert r.status_code == 401


def test_me_no_header(client, monkeypatch):
    """Sin header Authorization → 401."""
    r = client.get("/api/auth/me")

    assert r.status_code == 401
