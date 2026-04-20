"""Tests for auth configuration constants in config.py.

TDD — these tests were written BEFORE the implementation.
RED → GREEN cycle: run first to confirm failure, then implement, then confirm pass.
"""
import importlib
import os
import sys
import types
import logging
import pytest


@pytest.fixture(autouse=True)
def _restore_config():
    """Restore the config module after each test to prevent leaking state."""
    yield
    # Force re-import of config with original env so other test modules
    # that already hold a reference to config get the real values back.
    for key in list(sys.modules.keys()):
        if key == "config" or key.startswith("config."):
            del sys.modules[key]
    import config  # noqa: F401 — re-import to restore module-level state


def _reload_config(monkeypatch, env_overrides: dict) -> types.ModuleType:
    """Helper: set env vars, reload config module, return it."""
    # Remove any previously cached module
    for key in list(sys.modules.keys()):
        if key == "config" or key.startswith("config."):
            del sys.modules[key]

    for k, v in env_overrides.items():
        monkeypatch.setenv(k, v)

    import config as cfg
    return cfg


def _reload_config_without(monkeypatch, unset_keys: list[str], extra_env: dict | None = None) -> types.ModuleType:
    """Helper: unset env vars, optionally set others, reload config module."""
    for key in list(sys.modules.keys()):
        if key == "config" or key.startswith("config."):
            del sys.modules[key]

    for k in unset_keys:
        monkeypatch.delenv(k, raising=False)

    if extra_env:
        for k, v in extra_env.items():
            monkeypatch.setenv(k, v)

    import config as cfg
    return cfg


# ---------------------------------------------------------------------------
# TASK-2 tests
# ---------------------------------------------------------------------------

class TestJwtSecretKey:
    def test_default_jwt_secret_is_dev_default(self, monkeypatch):
        """JWT_SECRET_KEY default must be the dev placeholder string."""
        cfg = _reload_config_without(monkeypatch, ["JWT_SECRET_KEY"], {"ENVIRONMENT": "development"})
        assert cfg.JWT_SECRET_KEY == "dev-secret-DO-NOT-USE-IN-PRODUCTION"

    def test_jwt_secret_reads_from_env(self, monkeypatch):
        """When JWT_SECRET_KEY is set in env, config must use it."""
        cfg = _reload_config(monkeypatch, {"JWT_SECRET_KEY": "my-super-secret"})
        assert cfg.JWT_SECRET_KEY == "my-super-secret"

    def test_jwt_secret_dev_default_emits_warning(self, monkeypatch, caplog):
        """When JWT_SECRET_KEY is unset in development, a WARNING must be logged."""
        with caplog.at_level(logging.WARNING, logger="config"):
            _reload_config_without(monkeypatch, ["JWT_SECRET_KEY"], {"ENVIRONMENT": "development"})
        assert any("JWT_SECRET_KEY" in record.message for record in caplog.records), (
            "Expected a WARNING log about JWT_SECRET_KEY not set"
        )

    def test_jwt_secret_production_raises(self, monkeypatch):
        """When JWT_SECRET_KEY is unset in production, startup must raise ValueError."""
        for key in list(sys.modules.keys()):
            if key == "config" or key.startswith("config."):
                del sys.modules[key]

        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "production")

        with pytest.raises((ValueError, RuntimeError)):
            import config  # noqa: F401


class TestJwtAlgorithm:
    def test_jwt_algorithm_is_hs256(self, monkeypatch):
        """JWT_ALGORITHM must always be 'HS256'."""
        cfg = _reload_config_without(monkeypatch, [], {"ENVIRONMENT": "development"})
        assert cfg.JWT_ALGORITHM == "HS256"


class TestTokenExpiry:
    def test_default_access_token_expire_is_15(self, monkeypatch):
        """ACCESS_TOKEN_EXPIRE_MINUTES default must be 15."""
        cfg = _reload_config_without(
            monkeypatch, ["ACCESS_TOKEN_EXPIRE_MINUTES"], {"ENVIRONMENT": "development"}
        )
        assert cfg.ACCESS_TOKEN_EXPIRE_MINUTES == 15

    def test_default_refresh_token_expire_is_7(self, monkeypatch):
        """REFRESH_TOKEN_EXPIRE_DAYS default must be 7."""
        cfg = _reload_config_without(
            monkeypatch, ["REFRESH_TOKEN_EXPIRE_DAYS"], {"ENVIRONMENT": "development"}
        )
        assert cfg.REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_access_token_expire_reads_from_env(self, monkeypatch):
        """ACCESS_TOKEN_EXPIRE_MINUTES must be castable from env string to int."""
        cfg = _reload_config(monkeypatch, {"ACCESS_TOKEN_EXPIRE_MINUTES": "30", "ENVIRONMENT": "development"})
        assert cfg.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_refresh_token_expire_reads_from_env(self, monkeypatch):
        """REFRESH_TOKEN_EXPIRE_DAYS must be castable from env string to int."""
        cfg = _reload_config(monkeypatch, {"REFRESH_TOKEN_EXPIRE_DAYS": "14", "ENVIRONMENT": "development"})
        assert cfg.REFRESH_TOKEN_EXPIRE_DAYS == 14


class TestBcryptRounds:
    def test_default_bcrypt_rounds_is_12(self, monkeypatch):
        """BCRYPT_ROUNDS default must be 12."""
        cfg = _reload_config_without(
            monkeypatch, ["BCRYPT_ROUNDS"], {"ENVIRONMENT": "development"}
        )
        assert cfg.BCRYPT_ROUNDS == 12

    def test_bcrypt_rounds_reads_from_env(self, monkeypatch):
        """BCRYPT_ROUNDS must be castable from env string to int."""
        cfg = _reload_config(monkeypatch, {"BCRYPT_ROUNDS": "4", "ENVIRONMENT": "development"})
        assert cfg.BCRYPT_ROUNDS == 4


class TestCookieSecure:
    def test_cookie_secure_false_in_development(self, monkeypatch):
        """COOKIE_SECURE must be False when ENVIRONMENT=development."""
        cfg = _reload_config(monkeypatch, {"ENVIRONMENT": "development"})
        assert cfg.COOKIE_SECURE is False

    def test_cookie_secure_true_in_production(self, monkeypatch):
        """COOKIE_SECURE must be True when ENVIRONMENT=production."""
        cfg = _reload_config(
            monkeypatch,
            {
                "ENVIRONMENT": "production",
                "JWT_SECRET_KEY": "prod-secret-for-test",
            },
        )
        assert cfg.COOKIE_SECURE is True

    def test_cookie_secure_true_in_staging(self, monkeypatch):
        """COOKIE_SECURE must be True for any non-development ENVIRONMENT."""
        cfg = _reload_config(
            monkeypatch,
            {
                "ENVIRONMENT": "staging",
                "JWT_SECRET_KEY": "staging-secret-for-test",
            },
        )
        assert cfg.COOKIE_SECURE is True
