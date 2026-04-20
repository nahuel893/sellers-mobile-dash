# Environment Variables — Setup Guide

Copy the contents below to `.env` (project root) and `frontend/.env` as needed.

## Backend — project root `.env`

```bash
# =============================================================================
# PostgreSQL (medallion_db / Gold layer)
# =============================================================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gold_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# =============================================================================
# Auth
# =============================================================================
# Secret key for JWT signing. Generate with: openssl rand -hex 32
SECRET_KEY=your_jwt_secret_key_here

# Admin user seed (used by backend/scripts/seed_admin.py)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me_immediately
ADMIN_FULL_NAME=Administrador

# =============================================================================
# Seed script paths (optional overrides)
# =============================================================================
# Path to visitados.xlsx for backend/scripts/seed_visitas.py
# Default: ../sales-dashboard/data/visitados.xlsx (relative to project root)
# VISITAS_XLSX_PATH=/path/to/visitados.xlsx
```

## Frontend — `frontend/.env`

```bash
# =============================================================================
# Backend API base URL
# Leave empty to use the same origin (default for production / docker).
# Example for local dev: VITE_API_URL=http://localhost:8000
# =============================================================================
VITE_API_URL=

# =============================================================================
# MapTiler API key — REQUIRED for Mapa de Ventas
#
# Get a FREE key at https://www.maptiler.com/cloud/
# Free tier: 100,000 tile requests / month — enough for development.
#
# Steps:
#   1. Sign up at https://www.maptiler.com/cloud/
#   2. Dashboard → "Keys" → "New key"
#   3. Enable "Tiles API" access
#   4. Copy the key below
#
# Without this key the Mapa de Ventas page will show a blank basemap.
# =============================================================================
VITE_MAPTILER_KEY=your_maptiler_api_key_here
```
