-- =============================================================
-- Migration 003: operations.preventistas_supervisores
-- Target DB: sellers_app_db (APP_DB_* — NOT medallion_db)
-- Idempotent — safe to run multiple times.
--
-- psql -h $APP_DB_HOST -U $APP_DB_USER -d $APP_DB_NAME -f 003_preventistas_supervisores.sql
-- =============================================================

-- Operations schema (may already exist from 002)
CREATE SCHEMA IF NOT EXISTS operations;

-- preventistas_supervisores: mapeo vendedor → supervisor (RF-MIGRATION-PS)
-- PK: preventista (un preventista tiene un solo supervisor)
CREATE TABLE IF NOT EXISTS operations.preventistas_supervisores (
    preventista  VARCHAR(255) PRIMARY KEY,
    supervisor   VARCHAR(255) NOT NULL,
    updated_at   TIMESTAMP    DEFAULT NOW()
);
