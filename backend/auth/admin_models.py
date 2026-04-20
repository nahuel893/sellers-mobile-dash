"""Pydantic models for admin user management endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field


class UserListItem(BaseModel):
    """User row as returned in list and detail endpoints."""
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    sucursales: list[int] = Field(default_factory=list)


class UserCreate(BaseModel):
    """Payload for POST /api/admin/users."""
    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    sucursales: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """Payload for PATCH /api/admin/users/{id}.

    All fields are optional; only provided fields are applied.
    """
    full_name: str | None = Field(default=None, min_length=1)
    role: str | None = None
    is_active: bool | None = None
    sucursales: list[int] | None = None


class UserPasswordUpdate(BaseModel):
    """Payload for POST /api/admin/users/{id}/password."""
    password: str = Field(..., min_length=6)


class RoleItem(BaseModel):
    """A role entry returned by /api/admin/roles."""
    id: int
    name: str


class SucursalItem(BaseModel):
    """A sucursal entry returned by /api/admin/sucursales."""
    id: int
    descripcion: str
