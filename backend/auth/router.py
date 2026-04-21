"""Auth endpoints: login, refresh, logout, me.

Prefix: /api/auth
Tags: auth
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

import config
from auth.dependencies import get_current_active_user
from auth.jwt import create_access_token, create_refresh_token, decode_token
from auth.models import LoginRequest, TokenResponse, UserInDB, UserResponse
from auth.passwords import dummy_verify, verify_password
from auth.repository import (
    get_refresh_token,
    get_refresh_token_any,
    get_user_by_username,
    get_user_sucursales,
    revoke_all_user_tokens,
    revoke_refresh_token,
    save_refresh_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Roles que requieren sucursales asignadas para poder operar
_ROLES_REQUIEREN_SUCURSALES = {"supervisor", "vendedor"}

_COOKIE_NAME = "refresh_token"
_COOKIE_PATH = "/api/auth"
_COOKIE_MAX_AGE = 7 * 24 * 3600  # 7 días en segundos


def _hash_token(token: str) -> str:
    """SHA-256 del token (lo que se persiste en DB, nunca el token en claro)."""
    return hashlib.sha256(token.encode()).hexdigest()


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Setea el cookie de refresh token con atributos de seguridad."""
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite="lax",
        path=_COOKIE_PATH,
        max_age=_COOKIE_MAX_AGE,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Limpia el cookie de refresh token seteando max_age=0."""
    response.set_cookie(
        key=_COOKIE_NAME,
        value="",
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite="lax",
        path=_COOKIE_PATH,
        max_age=0,
    )


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response) -> TokenResponse:
    """Autentica usuario con username/password y devuelve JWT de acceso.

    Setea un refresh token como cookie httpOnly con path=/api/auth.
    """
    user = get_user_by_username(body.username)

    if user is None:
        # Llamar dummy_verify para prevenir timing attacks (user enumeration)
        dummy_verify()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    # RF-AUTH-002: is_active se valida ANTES que la password para que un atacante
    # no pueda distinguir (por timing) una cuenta inactiva de una credencial válida.
    if not user["is_active"]:
        dummy_verify()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
        )

    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    sucursales = get_user_sucursales(user["id"])

    if user["role_name"] in _ROLES_REQUIEREN_SUCURSALES and not sucursales:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sin sucursales asignadas",
        )

    # Para admin: sucursales=None (acceso irrestricto); para otros: la lista real
    sucursales_claim: list[int] | None = None if user["role_name"] not in _ROLES_REQUIEREN_SUCURSALES else sucursales

    access_token = create_access_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role_name"],
        sucursales=sucursales_claim,
    )

    refresh_token = create_refresh_token(user_id=user["id"])
    token_hash = _hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)

    save_refresh_token(
        user_id=user["id"],
        token_hash=token_hash,
        expires_at=expires_at,
    )

    _set_refresh_cookie(response, refresh_token)

    user_public = UserResponse(
        id=user["id"],
        username=user["username"],
        full_name=user["full_name"],
        role=user["role_name"],
        is_active=user["is_active"],
        sucursales=sucursales_claim,
    )

    return TokenResponse(access_token=access_token, user=user_public)


# ---------------------------------------------------------------------------
# POST /api/auth/refresh
# ---------------------------------------------------------------------------

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
) -> TokenResponse:
    """Rota el refresh token y devuelve un nuevo access token.

    El token anterior queda revocado en DB.
    """
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco no proporcionado",
        )

    # decode_token lanza HTTPException(401) si el token está expirado o es inválido
    try:
        payload = decode_token(refresh_token)
    except HTTPException:
        _clear_refresh_cookie(response)
        raise

    token_hash = _hash_token(refresh_token)
    db_token = get_refresh_token(token_hash)

    if db_token is None:
        # RF-SEC-009: si el token existe pero está revocado, es un intento de reuso
        # → revocamos TODOS los tokens activos del usuario como medida de seguridad.
        any_record = get_refresh_token_any(token_hash)
        if any_record is not None and any_record.get("revoked"):
            revoke_all_user_tokens(any_record["user_id"])

        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido",
        )

    user_id = int(payload["sub"])

    # Revocar el token antiguo
    revoke_refresh_token(token_hash)

    # Obtener datos del usuario para el nuevo access token
    # payload["username"] puede no estar en refresh tokens (solo "sub")
    # Buscar por ID no está en repository, pero el username está disponible
    # si el token fue creado con create_refresh_token (solo sub + type + exp)
    # Necesitamos el user; buscamos por id a través de la tabla de sucursales
    # o usamos directamente los datos del payload si están presentes.
    # create_refresh_token solo guarda "sub" (user_id), así que necesitamos
    # recargar el usuario desde la DB via username... pero no tenemos username.
    # Usamos db_token["user_id"] y buscamos el usuario.
    # El repositorio no tiene get_user_by_id, pero podemos resolverlo:
    # re-usamos la función existente pasando el user_id del token de DB.

    # Estrategia: el db_token tiene user_id; necesitamos el usuario completo.
    # Como no hay get_user_by_id, usamos el payload.get("username") si existe,
    # o get_user_by_username con el username del jwt (que en refresh solo tiene sub).
    # Solución pragmática: guardar el user_id del token y obtener datos mínimos
    # para crear el nuevo access token usando los claims que tengamos disponibles.
    # Para esto necesitamos el usuario; hacemos una query directa.

    user_id_from_token = db_token["user_id"]
    sucursales = get_user_sucursales(user_id_from_token)

    # Crear nuevos tokens — necesitamos username y role del usuario
    # El único path es buscar el usuario; usamos una query directa a través del módulo
    _new_user = _get_user_by_id(user_id_from_token)
    if _new_user is None:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    sucursales_claim: list[int] | None = (
        None if _new_user["role_name"] not in _ROLES_REQUIEREN_SUCURSALES else sucursales
    )

    new_access_token = create_access_token(
        user_id=_new_user["id"],
        username=_new_user["username"],
        role=_new_user["role_name"],
        sucursales=sucursales_claim,
    )

    new_refresh_token = create_refresh_token(user_id=_new_user["id"])
    new_hash = _hash_token(new_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)

    save_refresh_token(
        user_id=_new_user["id"],
        token_hash=new_hash,
        expires_at=expires_at,
    )

    _set_refresh_cookie(response, new_refresh_token)

    user_public = UserResponse(
        id=_new_user["id"],
        username=_new_user["username"],
        full_name=_new_user["full_name"],
        role=_new_user["role_name"],
        is_active=_new_user["is_active"],
        sucursales=sucursales_claim,
    )

    return TokenResponse(access_token=new_access_token, user=user_public)


def _get_user_by_id(user_id: int) -> dict | None:
    """Obtiene usuario por ID usando la conexión de DB directamente.

    Nota: repository no expone get_user_by_id, así que hacemos la query aquí.
    Si el test mockeó get_user_by_username, no llegamos a este punto (se usa
    desde refresh que mockea get_refresh_token y get_user_sucursales).
    """
    from data.app_db import get_connection as get_auth_connection, release_connection as release_auth_connection
    import psycopg2.extras

    conn = get_auth_connection()
    try:
        sql = """
            SELECT u.*, r.name AS role_name
            FROM auth.users u
            JOIN auth.roles r ON u.role_id = r.id
            WHERE u.id = %s
        """
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (user_id,))
            row = cur.fetchone()
            return dict(row) if row is not None else None
    finally:
        release_auth_connection(conn)


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------

@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
) -> dict:
    """Cierra sesión revocando el refresh token y limpiando el cookie.

    Es idempotente: si no hay cookie, devuelve 200 igual.
    """
    if refresh_token is not None:
        token_hash = _hash_token(refresh_token)
        revoke_refresh_token(token_hash)
        _clear_refresh_cookie(response)

    return {"message": "Sesión cerrada"}


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserResponse)
async def me(user: UserInDB = Depends(get_current_active_user)) -> UserResponse:
    """Devuelve los datos del usuario autenticado (sin password_hash)."""
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role_name,
        is_active=user.is_active,
        sucursales=user.sucursales,
    )
