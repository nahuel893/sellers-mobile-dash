"""Tests for backend/auth/passwords.py — password hashing and verification.

TDD — tests written BEFORE implementation.
RED → GREEN cycle: run first to confirm failure, then implement, then confirm pass.
"""
import importlib
import sys
import pytest


def _reload_passwords(monkeypatch, bcrypt_rounds: int = 4):
    """Helper: monkeypatch config.BCRYPT_ROUNDS, reload passwords module, return it."""
    # Reload config to ensure clean state
    for key in list(sys.modules.keys()):
        if key == "config" or key.startswith("config."):
            del sys.modules[key]
    for key in list(sys.modules.keys()):
        if key == "auth.passwords" or key == "auth" and "passwords" in key:
            del sys.modules[key]

    monkeypatch.setenv("BCRYPT_ROUNDS", str(bcrypt_rounds))
    monkeypatch.setenv("ENVIRONMENT", "development")

    # Remove cached passwords module
    for key in list(sys.modules.keys()):
        if key == "auth.passwords":
            del sys.modules[key]

    import auth.passwords as pwd
    return pwd


@pytest.fixture
def passwords(monkeypatch):
    """Fixture: load passwords module with BCRYPT_ROUNDS=4 for fast tests."""
    return _reload_passwords(monkeypatch, bcrypt_rounds=4)


class TestHashPassword:
    def test_hash_returns_bcrypt_prefix(self, passwords):
        """hash_password() must return a bcrypt hash starting with $2b$."""
        hashed = passwords.hash_password("mysecretpassword")
        assert hashed.startswith("$2b$"), (
            f"Expected bcrypt hash starting with '$2b$', got: {hashed[:10]!r}"
        )

    def test_hash_returns_string(self, passwords):
        """hash_password() must return a str."""
        result = passwords.hash_password("anypassword")
        assert isinstance(result, str)

    def test_hash_is_not_plain_text(self, passwords):
        """hash_password() must NOT return the plain password."""
        plain = "mysecretpassword"
        hashed = passwords.hash_password(plain)
        assert hashed != plain

    def test_hash_uses_config_rounds(self, monkeypatch):
        """hash_password() must use BCRYPT_ROUNDS from config (rounds embedded in hash)."""
        pwd = _reload_passwords(monkeypatch, bcrypt_rounds=4)
        hashed = pwd.hash_password("testpassword")
        # bcrypt hash format: $2b$<rounds>$<salt+hash>
        parts = hashed.split("$")
        # parts[0]='', parts[1]='2b', parts[2]='04' (zero-padded rounds)
        assert parts[2] == "04", (
            f"Expected bcrypt rounds '04' in hash, got '{parts[2]}'"
        )


class TestVerifyPassword:
    def test_verify_correct_password(self, passwords):
        """verify_password() must return True when plain matches the hash."""
        plain = "correct-password"
        hashed = passwords.hash_password(plain)
        assert passwords.verify_password(plain, hashed) is True

    def test_verify_wrong_password(self, passwords):
        """verify_password() must return False when plain does NOT match."""
        hashed = passwords.hash_password("correct-password")
        assert passwords.verify_password("wrong-password", hashed) is False

    def test_verify_returns_bool(self, passwords):
        """verify_password() must return a bool (not a truthy value)."""
        hashed = passwords.hash_password("password")
        result = passwords.verify_password("password", hashed)
        assert isinstance(result, bool)


class TestDummyVerify:
    def test_dummy_verify_does_not_raise(self, passwords):
        """dummy_verify() must not raise any exception."""
        try:
            passwords.dummy_verify()
        except Exception as exc:
            pytest.fail(f"dummy_verify() raised unexpectedly: {exc}")

    def test_dummy_verify_returns_none(self, passwords):
        """dummy_verify() must return None."""
        result = passwords.dummy_verify()
        assert result is None
