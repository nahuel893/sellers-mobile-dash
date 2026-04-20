"""Seed script: create or update the admin user in the auth schema.

Usage (from backend/):
    .venv/bin/python -m scripts.seed_admin

Configuration via environment variables:
    ADMIN_USERNAME   — username for the admin (default: "admin")
    ADMIN_PASSWORD   — REQUIRED; script exits if not set
    ADMIN_FULL_NAME  — display name (default: "Administrador")

PostgreSQL connection uses the same env vars as the main backend:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

The script is importable for testing (see tests/test_seed_admin.py).
The main entry-point is ``seed_admin()`` which can be called directly.
"""
from __future__ import annotations

import os
import pathlib
import sys

import psycopg2
from dotenv import load_dotenv

# Load .env from project root (3 levels above backend/scripts/seed_admin.py)
_env_path = pathlib.Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)


def seed_admin() -> None:
    """Create or update the admin user (idempotent).

    Raises:
        SystemExit: if ADMIN_PASSWORD is not set.
    """
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        print(
            "ERROR: ADMIN_PASSWORD environment variable is required.",
            file=sys.stderr,
        )
        sys.exit(1)

    username = os.getenv("ADMIN_USERNAME", "admin")
    full_name = os.getenv("ADMIN_FULL_NAME", "Administrador")

    # Import here so that test mocks on psycopg2.connect are applied before
    # the module-level pool in data.db is initialised.
    from auth.passwords import hash_password

    password_hash = hash_password(password)

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "gold_db"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

    with conn.cursor() as cur:
        # 1. Look up the 'admin' role id
        cur.execute(
            "SELECT id FROM auth.roles WHERE name = %s",
            ("admin",),
        )
        role_row = cur.fetchone()
        if role_row is None:
            print(
                "ERROR: Role 'admin' not found in auth.roles. "
                "Run migrations first.",
                file=sys.stderr,
            )
            sys.exit(1)

        role_id = role_row["id"] if isinstance(role_row, dict) else role_row[0]

        # 2. Upsert the user — ON CONFLICT keeps the operation idempotent
        cur.execute(
            """
            INSERT INTO auth.users (username, password_hash, full_name, role_id, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            ON CONFLICT (username) DO UPDATE
                SET password_hash = EXCLUDED.password_hash,
                    full_name     = EXCLUDED.full_name,
                    role_id       = EXCLUDED.role_id,
                    is_active     = TRUE
            """,
            (username, password_hash, full_name, role_id),
        )

    conn.commit()
    print(f"Admin user '{username}' created/updated successfully.")


if __name__ == "__main__":
    seed_admin()
