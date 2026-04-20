-- =============================================================
-- Migration 001: Auth schema
-- Idempotent — safe to run multiple times.
-- =============================================================

-- Auth schema isolation (RF-DB-001)
CREATE SCHEMA IF NOT EXISTS auth;

-- roles table (RF-DB-002)
CREATE TABLE IF NOT EXISTS auth.roles (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50)  UNIQUE NOT NULL,
    description TEXT
);

-- users table (RF-DB-003)
CREATE TABLE IF NOT EXISTS auth.users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(200) NOT NULL,
    role_id       INTEGER NOT NULL REFERENCES auth.roles(id),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

-- user_sucursales table (RF-DB-004)
CREATE TABLE IF NOT EXISTS auth.user_sucursales (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    id_sucursal INTEGER NOT NULL,
    UNIQUE(user_id, id_sucursal)
);

-- refresh_tokens table (RF-DB-005)
-- token_hash stores SHA-256 hex digest — raw token is NEVER stored.
CREATE TABLE IF NOT EXISTS auth.refresh_tokens (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL,
    expires_at  TIMESTAMP NOT NULL,
    revoked     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Seed default roles (RF-DB-002, RF-SEED-002)
-- ON CONFLICT DO NOTHING makes this idempotent.
INSERT INTO auth.roles (name, description) VALUES
    ('admin',      'Full access to all branches and admin features'),
    ('gerente',    'Full access to all branches, no admin features'),
    ('supervisor', 'Access restricted to assigned branches'),
    ('vendedor',   'Access restricted to own data within assigned branches')
ON CONFLICT (name) DO NOTHING;
