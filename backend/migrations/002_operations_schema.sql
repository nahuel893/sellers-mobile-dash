-- =============================================================
-- Migration 002: Operations schema — visitas_preventista table
-- Idempotent — safe to run multiple times.
-- =============================================================

-- Operations schema isolation
CREATE SCHEMA IF NOT EXISTS operations;

-- visitas_preventista table (RF-MIGRATION-001)
-- Stores field visits by preventistas, migrated from legacy visitados.xlsx.
-- Source: backend/scripts/seed_visitas.py
CREATE TABLE IF NOT EXISTS operations.visitas_preventista (
    id                   SERIAL PRIMARY KEY,
    id_cliente           INT NOT NULL,
    id_ruta              INT,
    ruta                 TEXT,
    fecha                DATE NOT NULL,
    hora_visita          TIME,
    hora_venta           TIME,
    hora_motivo          TIME,
    motivo               TEXT,
    visitado             BOOLEAN NOT NULL DEFAULT FALSE,
    latitud              DOUBLE PRECISION,
    longitud             DOUBLE PRECISION,
    domicilio            TEXT,
    sector               TEXT,
    descripcion_cliente  TEXT,
    foto_url             TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint enables idempotent upsert via ON CONFLICT
    CONSTRAINT uq_visitas_cliente_fecha_hora UNIQUE (id_cliente, fecha, hora_visita)
);

-- Index: date range queries (most common filter in recorrido endpoint)
CREATE INDEX IF NOT EXISTS idx_visitas_fecha
    ON operations.visitas_preventista (fecha);

-- Index: route + date queries (filtering by preventista/ruta for a given day)
CREATE INDEX IF NOT EXISTS idx_visitas_ruta_fecha
    ON operations.visitas_preventista (id_ruta, fecha);

-- Index: client lookup (joining with dim_cliente for coordinates)
CREATE INDEX IF NOT EXISTS idx_visitas_cliente
    ON operations.visitas_preventista (id_cliente);
