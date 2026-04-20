"""Admin endpoints for user management.

Prefix: /api/admin
Tags: admin

All endpoints require the ``admin`` role via ``require_role("admin")``.
"""
from __future__ import annotations

import psycopg2.errors
from fastapi import APIRouter, Depends, HTTPException, status

from auth.admin_models import (
    RoleItem,
    SucursalItem,
    UserCreate,
    UserListItem,
    UserPasswordUpdate,
    UserUpdate,
)
from auth.dependencies import require_role
from auth.models import UserInDB
from auth.passwords import hash_password
from auth.repository import (
    create_user,
    get_role_by_name,
    get_user_by_id,
    get_user_sucursales,
    list_roles,
    list_users,
    replace_user_sucursales,
    set_user_password,
    update_user,
)
from data.db import get_connection, release_connection

router = APIRouter(prefix="/api/admin", tags=["admin"])

_AdminUser = Depends(require_role("admin"))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _row_to_item(row: dict, sucursales: list[int]) -> UserListItem:
    """Convert a DB row dict to a UserListItem Pydantic model."""
    return UserListItem(
        id=row["id"],
        username=row["username"],
        full_name=row["full_name"],
        role=row["role_name"],
        is_active=row["is_active"],
        sucursales=sucursales,
    )


def list_sucursales_db(conn=None) -> list[dict]:
    """Query gold.dim_sucursal and return id + descripcion rows."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        import psycopg2.extras

        sql = """
            SELECT id_sucursal AS id, descripcion
            FROM gold.dim_sucursal
            ORDER BY id_sucursal
        """
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        if own_conn:
            release_connection(conn)


def _assert_not_self_modify(
    current_user: UserInDB,
    target_id: int,
    new_role: str | None,
    new_is_active: bool | None,
) -> None:
    """Raise 400 if the admin tries to demote or deactivate their own account."""
    if current_user.id != target_id:
        return

    if new_is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No podés desactivar tu propia cuenta.",
        )

    if new_role is not None and new_role != current_user.role_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No podés cambiar tu propio rol.",
        )


# ---------------------------------------------------------------------------
# GET /api/admin/users
# ---------------------------------------------------------------------------

@router.get("/users", response_model=list[UserListItem])
def admin_list_users(current_user: UserInDB = _AdminUser) -> list[UserListItem]:
    """List all users with their assigned sucursales."""
    rows = list_users()
    return [_row_to_item(row, get_user_sucursales(row["id"])) for row in rows]


# ---------------------------------------------------------------------------
# GET /api/admin/users/{user_id}
# ---------------------------------------------------------------------------

@router.get("/users/{user_id}", response_model=UserListItem)
def admin_get_user(user_id: int, current_user: UserInDB = _AdminUser) -> UserListItem:
    """Get a single user by ID."""
    row = get_user_by_id(user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    sucursales = get_user_sucursales(user_id)
    return _row_to_item(row, sucursales)


# ---------------------------------------------------------------------------
# POST /api/admin/users
# ---------------------------------------------------------------------------

@router.post("/users", response_model=UserListItem, status_code=status.HTTP_201_CREATED)
def admin_create_user(body: UserCreate, current_user: UserInDB = _AdminUser) -> UserListItem:
    """Create a new user."""
    role = get_role_by_name(body.role)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol desconocido: '{body.role}'.",
        )

    pw_hash = hash_password(body.password)

    try:
        new_id = create_user(
            username=body.username,
            password_hash=pw_hash,
            full_name=body.full_name,
            role_id=role["id"],
        )
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El nombre de usuario '{body.username}' ya existe.",
        )

    if body.sucursales:
        replace_user_sucursales(user_id=new_id, sucursal_ids=body.sucursales)

    row = get_user_by_id(new_id)
    sucursales = get_user_sucursales(new_id)
    return _row_to_item(row, sucursales)


# ---------------------------------------------------------------------------
# PATCH /api/admin/users/{user_id}
# ---------------------------------------------------------------------------

@router.patch("/users/{user_id}", response_model=UserListItem)
def admin_update_user(
    user_id: int,
    body: UserUpdate,
    current_user: UserInDB = _AdminUser,
) -> UserListItem:
    """Partially update a user (full_name, role, is_active, sucursales)."""
    row = get_user_by_id(user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    # Self-protection check
    _assert_not_self_modify(current_user, user_id, body.role, body.is_active)

    # Resolve new role_id if role name was provided
    new_role_id = row["role_id"]
    new_role_name = row["role_name"]
    if body.role is not None:
        role_obj = get_role_by_name(body.role)
        if role_obj is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol desconocido: '{body.role}'.",
            )
        new_role_id = role_obj["id"]
        new_role_name = role_obj["name"]

    new_full_name = body.full_name if body.full_name is not None else row["full_name"]
    new_is_active = body.is_active if body.is_active is not None else row["is_active"]

    update_user(
        user_id=user_id,
        full_name=new_full_name,
        role_id=new_role_id,
        is_active=new_is_active,
    )

    if body.sucursales is not None:
        replace_user_sucursales(user_id=user_id, sucursal_ids=body.sucursales)

    # Return updated state
    updated_row = get_user_by_id(user_id)
    sucursales = get_user_sucursales(user_id)
    return _row_to_item(updated_row, sucursales)


# ---------------------------------------------------------------------------
# POST /api/admin/users/{user_id}/password
# ---------------------------------------------------------------------------

@router.post("/users/{user_id}/password")
def admin_reset_password(
    user_id: int,
    body: UserPasswordUpdate,
    current_user: UserInDB = _AdminUser,
) -> dict:
    """Reset a user's password (admin sets it directly)."""
    row = get_user_by_id(user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    pw_hash = hash_password(body.password)
    set_user_password(user_id=user_id, password_hash=pw_hash)

    return {"message": "Contraseña actualizada."}


# ---------------------------------------------------------------------------
# GET /api/admin/roles
# ---------------------------------------------------------------------------

@router.get("/roles", response_model=list[RoleItem])
def admin_list_roles(current_user: UserInDB = _AdminUser) -> list[RoleItem]:
    """List all available roles."""
    rows = list_roles()
    return [RoleItem(id=row["id"], name=row["name"]) for row in rows]


# ---------------------------------------------------------------------------
# GET /api/admin/sucursales
# ---------------------------------------------------------------------------

@router.get("/sucursales", response_model=list[SucursalItem])
def admin_list_sucursales(current_user: UserInDB = _AdminUser) -> list[SucursalItem]:
    """List all sucursales from gold.dim_sucursal."""
    rows = list_sucursales_db()
    return [SucursalItem(id=row["id"], descripcion=row["descripcion"]) for row in rows]
