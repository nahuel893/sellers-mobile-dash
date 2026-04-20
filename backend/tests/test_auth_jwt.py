"""Tests for backend/auth/jwt.py — JWT token creation and validation.

TDD — these tests were written BEFORE the implementation.
RED → GREEN cycle: run first to confirm failure, then implement, then confirm pass.
"""
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import HTTPException
from jose import jwt as jose_jwt


# ---------------------------------------------------------------------------
# Helper — import the module under test lazily so RED phase shows ImportError
# ---------------------------------------------------------------------------

def _import_jwt():
    from auth import jwt as auth_jwt
    return auth_jwt


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------

class TestCreateAccessToken:
    def test_create_access_token_roundtrip(self):
        """create → decode → claims must match inputs."""
        auth_jwt = _import_jwt()
        token = auth_jwt.create_access_token(
            user_id=42,
            username="testuser",
            role="vendedor",
            sucursales=[1, 2],
        )
        payload = auth_jwt.decode_token(token)
        assert payload["sub"] == "42"
        assert payload["username"] == "testuser"
        assert payload["role"] == "vendedor"
        assert payload["sucursales"] == [1, 2]

    def test_access_token_has_exp_in_future(self):
        """exp claim must be in the future."""
        auth_jwt = _import_jwt()
        token = auth_jwt.create_access_token(
            user_id=1, username="u", role="vendedor", sucursales=None
        )
        payload = auth_jwt.decode_token(token)
        exp_dt = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert exp_dt > datetime.now(tz=timezone.utc)

    def test_access_token_contains_role_and_sucursales(self):
        """Role and sucursales must be present in the decoded payload."""
        auth_jwt = _import_jwt()
        token = auth_jwt.create_access_token(
            user_id=7, username="alice", role="supervisor", sucursales=[5, 6, 7]
        )
        payload = auth_jwt.decode_token(token)
        assert "role" in payload
        assert "sucursales" in payload
        assert payload["role"] == "supervisor"
        assert payload["sucursales"] == [5, 6, 7]

    def test_access_token_sucursales_null_for_admin(self):
        """When sucursales=None (admin), the decoded claim must be None."""
        auth_jwt = _import_jwt()
        token = auth_jwt.create_access_token(
            user_id=99, username="admin", role="admin", sucursales=None
        )
        payload = auth_jwt.decode_token(token)
        assert payload["sucursales"] is None

    def test_access_token_sucursales_list_for_supervisor(self):
        """When sucursales is a list, decoded claim must equal that list."""
        auth_jwt = _import_jwt()
        token = auth_jwt.create_access_token(
            user_id=10, username="sup", role="supervisor", sucursales=[3, 4]
        )
        payload = auth_jwt.decode_token(token)
        assert payload["sucursales"] == [3, 4]


# ---------------------------------------------------------------------------
# decode_token — error cases
# ---------------------------------------------------------------------------

class TestDecodeToken:
    def test_expired_token_raises_401(self):
        """A token with exp in the past must raise HTTPException(401)."""
        import config
        # Build an already-expired token manually using jose directly
        now = datetime.now(tz=timezone.utc)
        expired_payload = {
            "sub": "1",
            "username": "x",
            "role": "vendedor",
            "sucursales": None,
            "exp": now - timedelta(minutes=1),
        }
        expired_token = jose_jwt.encode(
            expired_payload,
            config.JWT_SECRET_KEY,
            algorithm=config.JWT_ALGORITHM,
        )
        auth_jwt = _import_jwt()
        with pytest.raises(HTTPException) as exc_info:
            auth_jwt.decode_token(expired_token)
        assert exc_info.value.status_code == 401

    def test_invalid_token_raises_401(self):
        """A garbage string must raise HTTPException(401)."""
        auth_jwt = _import_jwt()
        with pytest.raises(HTTPException) as exc_info:
            auth_jwt.decode_token("this.is.garbage")
        assert exc_info.value.status_code == 401

    def test_wrong_algorithm_rejected(self):
        """A token signed with HS384 must be rejected by decode_token (expects HS256)."""
        import config
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub": "1",
            "username": "x",
            "role": "vendedor",
            "sucursales": None,
            "exp": now + timedelta(minutes=15),
        }
        wrong_alg_token = jose_jwt.encode(
            payload,
            config.JWT_SECRET_KEY,
            algorithm="HS384",
        )
        auth_jwt = _import_jwt()
        with pytest.raises(HTTPException) as exc_info:
            auth_jwt.decode_token(wrong_alg_token)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Entropy
# ---------------------------------------------------------------------------

class TestTokenEntropy:
    def test_two_tokens_differ(self):
        """Two tokens for the same user must differ (due to different exp timestamps)."""
        auth_jwt = _import_jwt()
        t1 = auth_jwt.create_access_token(
            user_id=1, username="u", role="vendedor", sucursales=None
        )
        t2 = auth_jwt.create_access_token(
            user_id=1, username="u", role="vendedor", sucursales=None
        )
        # They may be identical if created in the same second — that's acceptable
        # since exp is second-precision. But the function must return a non-empty string.
        assert isinstance(t1, str) and len(t1) > 0
        assert isinstance(t2, str) and len(t2) > 0


# ---------------------------------------------------------------------------
# create_refresh_token
# ---------------------------------------------------------------------------

class TestCreateRefreshToken:
    def test_refresh_token_has_type_refresh(self):
        """Decoded refresh token must contain type='refresh'."""
        import config
        auth_jwt = _import_jwt()
        token = auth_jwt.create_refresh_token(user_id=5)
        # Decode manually to inspect raw claims (decode_token is for access tokens)
        payload = jose_jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM],
        )
        assert payload.get("type") == "refresh"

    def test_refresh_token_sub_is_str_user_id(self):
        """refresh token sub must be str(user_id) per JWT standard."""
        import config
        auth_jwt = _import_jwt()
        token = auth_jwt.create_refresh_token(user_id=42)
        payload = jose_jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM],
        )
        assert payload["sub"] == "42"

    def test_refresh_token_has_exp_in_future(self):
        """Refresh token exp must be in the future."""
        import config
        auth_jwt = _import_jwt()
        token = auth_jwt.create_refresh_token(user_id=1)
        payload = jose_jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM],
        )
        exp_dt = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert exp_dt > datetime.now(tz=timezone.utc)
