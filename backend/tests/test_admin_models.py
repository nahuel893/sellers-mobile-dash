"""Tests for admin Pydantic models in auth/admin_models.py.

Validates field constraints, defaults, and serialization behavior.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestUserListItem:
    def test_valid_item(self):
        """UserListItem accepts all expected fields."""
        from auth.admin_models import UserListItem

        item = UserListItem(
            id=1,
            username="juan",
            full_name="Juan Pérez",
            role="vendedor",
            is_active=True,
            sucursales=[10, 20],
        )
        assert item.id == 1
        assert item.sucursales == [10, 20]

    def test_sucursales_default_empty(self):
        """sucursales defaults to empty list when not provided."""
        from auth.admin_models import UserListItem

        item = UserListItem(id=1, username="u", full_name="F", role="admin", is_active=True)
        assert item.sucursales == []


class TestUserCreate:
    def test_valid_create(self):
        """UserCreate accepts all valid fields."""
        from auth.admin_models import UserCreate

        payload = UserCreate(
            username="newuser",
            password="secret123",
            full_name="New User",
            role="vendedor",
            sucursales=[1, 2],
        )
        assert payload.username == "newuser"
        assert payload.sucursales == [1, 2]

    def test_password_min_length(self):
        """password must be at least 6 characters."""
        from auth.admin_models import UserCreate

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="u", password="123", full_name="F", role="vendedor")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_username_required(self):
        """username is required."""
        from auth.admin_models import UserCreate

        with pytest.raises(ValidationError):
            UserCreate(password="secret123", full_name="F", role="vendedor")

    def test_sucursales_default_empty(self):
        """sucursales defaults to [] when not supplied."""
        from auth.admin_models import UserCreate

        payload = UserCreate(username="u", password="secret123", full_name="F", role="admin")
        assert payload.sucursales == []


class TestUserUpdate:
    def test_all_optional(self):
        """UserUpdate can be instantiated with no fields — all optional."""
        from auth.admin_models import UserUpdate

        upd = UserUpdate()
        assert upd.full_name is None
        assert upd.role is None
        assert upd.is_active is None
        assert upd.sucursales is None

    def test_partial_update(self):
        """Only provided fields are set."""
        from auth.admin_models import UserUpdate

        upd = UserUpdate(is_active=False)
        assert upd.is_active is False
        assert upd.role is None

    def test_full_name_min_length(self):
        """full_name cannot be empty string when provided."""
        from auth.admin_models import UserUpdate

        with pytest.raises(ValidationError):
            UserUpdate(full_name="")


class TestUserPasswordUpdate:
    def test_valid_password(self):
        """UserPasswordUpdate accepts passwords >= 6 chars."""
        from auth.admin_models import UserPasswordUpdate

        upd = UserPasswordUpdate(password="newsecret")
        assert upd.password == "newsecret"

    def test_password_too_short(self):
        """Raises ValidationError when password is < 6 chars."""
        from auth.admin_models import UserPasswordUpdate

        with pytest.raises(ValidationError):
            UserPasswordUpdate(password="abc")


class TestRoleItem:
    def test_valid(self):
        """RoleItem accepts id and name."""
        from auth.admin_models import RoleItem

        role = RoleItem(id=1, name="admin")
        assert role.name == "admin"


class TestSucursalItem:
    def test_valid(self):
        """SucursalItem accepts id and descripcion."""
        from auth.admin_models import SucursalItem

        item = SucursalItem(id=5, descripcion="Sucursal Norte")
        assert item.id == 5
        assert item.descripcion == "Sucursal Norte"
