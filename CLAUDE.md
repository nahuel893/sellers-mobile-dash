# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dash-based mobile-first sales dashboard ("Avance Preventa") for beverage company sales reps (preventistas). Displays sales progress vs quotas by brand group, with trend projections to end-of-month. UI, comments, and variable names are in **Spanish**.

**Planned migration**: FastAPI + React (see `.claude/memory/MIGRATION_FASTAPI_REACT.md` for full plan).

## Commands

```bash
python run.py                        # Dev server at http://localhost:8050
pytest                               # Run all tests (26 tests)
pytest tests/test_ventas_service.py -v  # Single test file
pytest tests/ -k test_falta          # Filter by keyword
pip install -r requirements.txt      # Install dependencies
```

Requires `.env` with PostgreSQL credentials (see `.env.example`). If DB is unreachable, falls back to mock data automatically.

## Architecture

**Stack**: Dash 2.18 + Plotly + dash-bootstrap-components + Pandas + psycopg2 + python-dotenv

### Data Flow

```
PostgreSQL (Gold DW) + CSV quotas (data/cupos.csv)
        ↓
  src/data/data_loader.py   — Orchestrates: queries DB, merges with cupos CSV, fallback to mock_data.py
        ↓
  src/services/ventas_service.py  — Business logic: filtering, aggregation, trend calculations
        ↓
  src/callbacks/dashboard_callbacks.py → views.py  — Route dispatch + component assembly
        ↓
  src/layouts/                — Dash HTML components (header, filters, gauges, map)
```

### Key Directories

- `src/data/` — DB connection pooling (`db.py`), SQL queries (`queries.py`), data loading/caching (`data_loader.py`), mock fallback (`mock_data.py`)
- `src/services/` — Business logic: sales aggregation, trend math (`ventas_service.py`)
- `src/callbacks/` — Dash callback registration (`dashboard_callbacks.py`) and view builders (`views.py`)
- `src/layouts/` — UI components: header, filter dropdowns, gauge charts, customer map
- `assets/` — Static CSS (`styles.css`, mobile-first) and client-side JS (`carousel.js`)
- `data/` — CSV quota files (`cupos.csv`), source spreadsheets, `supervisores.xlsx`
- `scripts/procesar_cupos.py` — Excel → cupos.csv converter
- `config.py` — Brand/category mappings, color scheme, working-day calculations

### Routing

Client-side via `dcc.Location` + callback router. `suppress_callback_exceptions=True` for dynamic layout. URL patterns:
- `/` — Home index with filter dropdowns
- `/vendedor/<SLUG>` — Individual vendor detail
- `/supervisor/<SLUG>?sucursal=ID` — Supervisor aggregate view
- `/sucursal/<ID>` — Branch view
- `/mapa/<SLUG>?sucursal=ID` — Customer map for vendor
- `/health` — Flask health check (bypasses Dash)

Slug encoding: spaces → hyphens, literal hyphens → `%2D` (see `to_slug()`/`from_slug()` in `views.py`).

### Data Caching

`data_loader.py` caches the merged DataFrame daily (`_df_cache` + `_df_cache_date`). `config.py` caches working-day calculations per day. Both auto-refresh when the date changes.

## Business Rules

- **Tendencia** = ventas × (dias_habiles / dias_transcurridos) — no rounding
- **% Tendencia** = tendencia / cupo × 100 — no rounding, display with 1 decimal
- **Falta** = cupo - ventas
- Performance colors: green ≥80%, yellow 70-80%, red <70% (`config.py:color_por_rendimiento`)
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

## Known Issues

- `responsive=True` on `dcc.Graph` breaks gauges — do NOT use
- Too many Plotly graphs on home page (candidate for lazy loading)
