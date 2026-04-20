"""Pydantic models for authentication and authorization."""
from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Credenciales para login."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """Datos públicos del usuario autenticado (sin password_hash)."""
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    sucursales: list[int] | None = None


class TokenResponse(BaseModel):
    """JWT token + datos del usuario devueltos tras login/refresh."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse | None = None


class TokenPayload(BaseModel):
    """Payload decodificado del JWT."""
    sub: str
    username: str | None = None
    role: str | None = None
    sucursales: list[int] | None = None
    type: str | None = None
    exp: int | None = None


class UserInDB(BaseModel):
    """Modelo interno de usuario — NUNCA exponer en respuestas de API."""
    id: int
    username: str
    password_hash: str
    full_name: str
    role_id: int
    role_name: str
    is_active: bool
    sucursales: list[int] | None = None
