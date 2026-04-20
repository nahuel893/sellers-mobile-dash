"""Tests for auth Pydantic models — TASK-5."""
import pytest
from pydantic import ValidationError

from auth.models import (
    LoginRequest,
    TokenPayload,
    TokenResponse,
    UserInDB,
    UserResponse,
)


# ---------------------------------------------------------------------------
# LoginRequest
# ---------------------------------------------------------------------------

def test_login_request_valid():
    req = LoginRequest(username="john", password="secret")
    assert req.username == "john"
    assert req.password == "secret"


def test_login_request_empty_username_raises():
    with pytest.raises(ValidationError):
        LoginRequest(username="", password="secret")


def test_login_request_empty_password_raises():
    with pytest.raises(ValidationError):
        LoginRequest(username="john", password="")


# ---------------------------------------------------------------------------
# TokenResponse
# ---------------------------------------------------------------------------

def test_token_response_default_type_is_bearer():
    token = TokenResponse(access_token="abc123")
    assert token.token_type == "bearer"


def test_token_response_custom_type():
    token = TokenResponse(access_token="abc123", token_type="jwt")
    assert token.token_type == "jwt"


# ---------------------------------------------------------------------------
# UserResponse
# ---------------------------------------------------------------------------

def test_user_response_fields():
    user = UserResponse(
        id=1,
        username="john",
        full_name="John Doe",
        role="vendedor",
        is_active=True,
        sucursales=[1, 2],
    )
    assert user.id == 1
    assert user.username == "john"
    assert user.full_name == "John Doe"
    assert user.role == "vendedor"
    assert user.is_active is True
    assert user.sucursales == [1, 2]


def test_user_response_sucursales_none():
    user = UserResponse(
        id=1,
        username="john",
        full_name="John Doe",
        role="admin",
        is_active=True,
        sucursales=None,
    )
    assert user.sucursales is None


# ---------------------------------------------------------------------------
# UserInDB
# ---------------------------------------------------------------------------

def test_user_in_db_has_password_hash():
    user = UserInDB(
        id=1,
        username="john",
        password_hash="$2b$12$hashed",
        full_name="John Doe",
        role_id=2,
        role_name="vendedor",
        is_active=True,
    )
    assert user.password_hash == "$2b$12$hashed"


def test_user_in_db_not_in_token_response_fields():
    """password_hash must NOT appear in TokenResponse (internal model isolation)."""
    token_fields = set(TokenResponse.model_fields.keys())
    assert "password_hash" not in token_fields


# ---------------------------------------------------------------------------
# TokenPayload
# ---------------------------------------------------------------------------

def test_token_payload_optional_fields():
    payload = TokenPayload(sub="john")
    assert payload.sub == "john"
    assert payload.username is None
    assert payload.role is None
    assert payload.sucursales is None
    assert payload.type is None
    assert payload.exp is None


def test_token_payload_all_fields():
    payload = TokenPayload(
        sub="john",
        username="john",
        role="supervisor",
        sucursales=[3],
        type="access",
        exp=9999999999,
    )
    assert payload.role == "supervisor"
    assert payload.sucursales == [3]
    assert payload.exp == 9999999999
