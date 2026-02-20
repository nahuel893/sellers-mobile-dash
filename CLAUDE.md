# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mobile-first sales dashboard ("Avance Preventa") for beverage company sales reps. Displays sales progress vs quotas by brand group, with trend projections. UI, comments, and variable names are in **Spanish**.

**Architecture**: FastAPI backend (REST API) + React frontend (SPA). Legacy Dash app still available for comparison.

## Commands

### Backend (FastAPI)
```bash
cd backend && .venv/bin/uvicorn main:app --reload --port 8000  # Dev server
cd backend && .venv/bin/pytest -v                                # 39 tests
cd backend && .venv/bin/pytest tests/test_api.py -v              # Single file
cd backend && .venv/bin/pytest -k test_falta                     # By keyword
```

### Frontend (React)
```bash
cd frontend && npm run dev          # Dev server at http://localhost:5173
cd frontend && npm run build        # Production build → dist/
cd frontend && npx tsc --noEmit     # Type check
```

### Legacy (Dash)
```bash
pip install -r requirements.txt
python run.py                       # Dev server at http://localhost:8050
```

Requires `.env` with PostgreSQL credentials (see `.env.example`). If DB is unreachable, backend falls back to mock data automatically (except mapa endpoint).

## Architecture

### Backend (`backend/`)

**Stack**: FastAPI + Pydantic v2 + Pandas + psycopg2

```
backend/
├── main.py              # FastAPI app, CORS, lifespan, router registration
├── schemas.py           # Pydantic response models
├── dependencies.py      # DI: get_df() → cached DataFrame
├── utils.py             # to_slug/from_slug, find_sucursal
├── config.py            # Brand/category mappings, working-day calculations
├── routers/
│   ├── dashboard.py     # /api/dashboard, /api/vendedor, /api/supervisor, /api/sucursal
│   ├── mapa.py          # /api/mapa/{slug} (direct DB query)
│   └── config_router.py # /api/config/dias-habiles
├── data/
│   ├── data_loader.py   # Orchestrates: DB query + cupos merge + fallback
│   ├── db.py            # PostgreSQL connection pool
│   ├── queries.py       # SQL queries
│   └── mock_data.py     # Mock data fallback
├── services/
│   └── ventas_service.py # Business logic: filtering, aggregation, trends
└── tests/               # 39 tests (pytest + httpx TestClient)
```

### Frontend (`frontend/`)

**Stack**: React 19 + TypeScript + Vite + Tailwind CSS v3 + TanStack Query v5 + React Router v7 + Leaflet

```
frontend/src/
├── components/          # 13 reusable components (gauges, carousel, filters, map)
├── pages/               # 6 pages (Home, Vendedor, Supervisor, Sucursal, Mapa, 404)
├── hooks/               # 8 TanStack Query hooks
├── lib/                 # api-client.ts, format.ts, constants.ts
└── types/               # TypeScript interfaces (1:1 with schemas.py)
```

### Legacy Dash (`src/`)

Still functional at port 8050. Not modified during migration.

```
src/
├── data/                # DB + data loading (shared logic, copied to backend/)
├── services/            # Business logic (copied to backend/)
├── callbacks/           # Dash callbacks + view builders
└── layouts/             # Dash HTML components (gauges, filters, header)
```

### Data Flow

```
PostgreSQL (Gold DW) + CSV quotas (data/cupos.csv)
        ↓
  backend/data/data_loader.py   — Query DB, merge cupos, fallback mock
        ↓
  backend/services/ventas_service.py  — Filter, aggregate, trend calculations
        ↓
  backend/routers/  — REST endpoints (JSON responses)
        ↓
  frontend/src/hooks/  — TanStack Query (fetch + cache)
        ↓
  frontend/src/components/  — React components (SVG gauges, carousels, map)
```

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/health` | Health check |
| GET | `/api/config/dias-habiles` | Working days info |
| GET | `/api/sucursales` | List branches |
| GET | `/api/supervisores?sucursal=` | Supervisors by branch |
| GET | `/api/vendedores?supervisor=&sucursal=` | Vendors by supervisor |
| GET | `/api/dashboard?supervisor=&sucursal=` | Full dashboard (home) |
| GET | `/api/vendedor/{slug}` | Vendor detail |
| GET | `/api/supervisor/{slug}?sucursal=` | Supervisor detail |
| GET | `/api/sucursal/{id}` | Branch detail |
| GET | `/api/mapa/{slug}?sucursal=` | Customer coordinates |

Interactive docs: `http://localhost:8000/docs`

## Frontend Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Cascading filters + gauges + vendor carousels |
| `/vendedor/{slug}` | Vendedor | All categories stacked vertically |
| `/supervisor/{slug}` | Supervisor | Category toggle + vendor blocks with sync |
| `/sucursal/{id}` | Sucursal | Branch summary + supervisor blocks |
| `/mapa/{slug}` | Mapa | Leaflet map with customer markers |

## Slug Encoding

Spaces → hyphens, literal hyphens → `%2D`. See `to_slug()`/`from_slug()` in `backend/utils.py` and `frontend/src/lib/format.ts`.

## Business Rules

- **Tendencia** = ventas × (dias_habiles / dias_transcurridos) — no rounding
- **% Tendencia** = tendencia / cupo × 100 — no rounding, display with 1 decimal
- **Falta** = cupo - ventas
- Performance colors: green ≥80%, yellow 70-80%, red <70%
- `DIAS_TRANSCURRIDOS` and `DIAS_RESTANTES` have minimum of 1 (avoid division by zero)

## Quota Logic (Important)

Quotas from `data/cupos.csv`. The `TOTAL_CERVEZAS` row is the **aggregate beer quota** — do NOT sum individual brand quotas to get beer total. `SALTA CAUTIVA1` has no individual gauge but its sales count toward the beer total.

## Data Merge Details

- OUTER merge ventas + cupos on `[vendedor, sucursal, categoria, grupo_marca]`
- Sentinel `__NONE__` for `grupo_marca=None` (NaN != NaN in pandas merge)
- TOTAL_CERVEZAS handled separately from merge, added afterward with ventas=0
- Supervisor lookup via vectorized merge (not apply/lambda)
- `_EXPECTED_ERRORS` triggers fallback to mock; unexpected errors re-raise

## Database

PostgreSQL Gold layer (Medallion Architecture). Star schema with `fact_ventas` (7M+ rows). Dimensions: `dim_articulo`, `dim_cliente`, `dim_vendedor`, `dim_sucursal`. **Critical**: composite join keys `(id_vendedor, id_sucursal)` and `(id_cliente, id_sucursal)`. Column is `dim_sucursal.descripcion` (NOT `des_sucursal`). See `DB_CONTEXT_GOLD.md` for full schema.

## Key Frontend Components

| Component | Purpose |
|-----------|---------|
| `GaugeSvg` | Core SVG semicircular gauge (replaces Plotly, ~1KB each) |
| `GaugeTotal` | Large gauge + 4 metrics (Vendido, Cupo, Falta, Tendencia) |
| `RingMarca` | Brand card with color dot + small gauge + 3 metrics |
| `CategorySlide` | CERVEZAS = gauge + brand grid; others = gauge only |
| `CategoryCarousel` | Scroll-snap horizontal + dots + globalSlideIndex sync |
| `CategoryToggle` | Pill buttons to sync all carousels to same category |
| `SummaryBlock` | Sucursal/supervisor aggregate block with carousel |
| `VendorBlock` | Vendor name-link + carousel |
| `CustomerMap` | Leaflet wrapper with markers + popups |

## Known Issues

- Mapa endpoint requires live PostgreSQL connection (no mock fallback)
- `responsive=True` on Dash `dcc.Graph` breaks gauges (legacy only)
