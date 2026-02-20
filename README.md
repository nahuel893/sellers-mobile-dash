# Avance Preventa - Sales Dashboard

Dashboard mobile-first para preventistas de empresa de bebidas. Muestra el avance de ventas vs cupo por grupo de marca, con porcentajes en **tendencia** (proyeccion a fin de mes).

## Preview

<p align="center">
  <img src="docs/screenshot_mobile.png" alt="Dashboard mobile" width="300">
</p>

## Arquitectura

El proyecto tiene dos implementaciones que corren en paralelo:

| Capa | Legacy (Dash) | Nueva (FastAPI + React) |
|------|---------------|------------------------|
| Backend | Dash 2.18 + Plotly | FastAPI + Pydantic |
| Frontend | Server-rendered HTML | React 19 + TypeScript + Tailwind |
| Gauges | Plotly Indicator (~3MB) | SVG custom (~1KB c/u) |
| Mapas | Plotly Scattermapbox | Leaflet (~40KB) |
| Puerto | 8050 | 8000 (API) + 5173 (dev) |

### Data Flow

```
PostgreSQL (Gold DW) + CSV quotas (data/cupos.csv)
        |
        v
backend/data/data_loader.py  -- Queries DB, merge cupos, fallback mock
        |
        v
backend/services/ventas_service.py  -- Filtrado, agregacion, tendencias
        |
        v
backend/routers/  -- Endpoints REST (FastAPI)
        |
        v
frontend/src/  -- React SPA (TanStack Query + React Router)
```

### Estructura del proyecto

```
seller-mobile-dashboard/
├── backend/                    # FastAPI REST API
│   ├── main.py                 # App FastAPI + CORS + routers
│   ├── schemas.py              # Pydantic response models
│   ├── dependencies.py         # DI: get_df()
│   ├── utils.py                # to_slug/from_slug helpers
│   ├── config.py               # Marcas, colores, dias habiles
│   ├── routers/
│   │   ├── dashboard.py        # /api/dashboard, /api/vendedor, etc.
│   │   ├── mapa.py             # /api/mapa/{slug}
│   │   └── config_router.py    # /api/config/dias-habiles
│   ├── data/
│   │   ├── data_loader.py      # Carga y cache de datos
│   │   ├── db.py               # Connection pool PostgreSQL
│   │   ├── queries.py          # SQL queries
│   │   └── mock_data.py        # Datos mock (fallback)
│   ├── services/
│   │   └── ventas_service.py   # Logica de negocio
│   ├── tests/                  # 39 tests (pytest)
│   └── requirements.txt
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── components/         # 13 componentes reutilizables
│   │   ├── pages/              # 6 paginas (Home, Vendedor, Supervisor, Sucursal, Mapa, 404)
│   │   ├── hooks/              # 8 hooks TanStack Query
│   │   ├── lib/                # API client, utilidades, constantes
│   │   └── types/              # Interfaces TypeScript
│   ├── package.json
│   └── vite.config.ts          # Proxy /api -> localhost:8000
├── src/                        # [Legacy] Dash app
├── run.py                      # [Legacy] Dash entry point
├── data/                       # CSVs de cupos
└── .env                        # Credenciales PostgreSQL
```

## Quick Start

### Requisitos

- Python 3.11+
- Node.js 18+
- PostgreSQL (opcional — usa mock data si no hay conexion)

### Setup

```bash
# 1. Backend: crear venv e instalar dependencias
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Frontend: instalar dependencias
cd frontend
npm install

# 3. Configurar DB (opcional)
cp .env.example .env
# Editar .env con credenciales PostgreSQL
```

### Levantar el proyecto

```bash
# Terminal 1: Backend (API)
cd backend && .venv/bin/uvicorn main:app --reload --port 8000

# Terminal 2: Frontend (React dev server)
cd frontend && npm run dev
```

Abrir **http://localhost:5173** en el navegador.

Para exponer en red local: `--host 0.0.0.0` en uvicorn.

### Legacy (Dash)

```bash
pip install -r requirements.txt
python run.py    # http://localhost:8050
```

## API Endpoints

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/config/dias-habiles` | Dias habiles del mes |
| GET | `/api/sucursales` | Lista de sucursales |
| GET | `/api/supervisores?sucursal=` | Supervisores por sucursal |
| GET | `/api/vendedores?supervisor=&sucursal=` | Vendedores por supervisor |
| GET | `/api/dashboard?supervisor=&sucursal=` | Dashboard completo (home) |
| GET | `/api/vendedor/{slug}` | Detalle vendedor |
| GET | `/api/supervisor/{slug}?sucursal=` | Detalle supervisor |
| GET | `/api/sucursal/{id}` | Detalle sucursal |
| GET | `/api/mapa/{slug}?sucursal=` | Clientes con coordenadas |

Documentacion interactiva: **http://localhost:8000/docs**

## Frontend - Paginas

| Ruta | Pagina | Descripcion |
|------|--------|-------------|
| `/` | Home | Filtros cascading + gauges + carruseles vendedores |
| `/vendedor/{slug}` | Vendedor | Categorias apiladas verticalmente con gauges |
| `/supervisor/{slug}` | Supervisor | Toggle categorias + bloques vendedores con sync |
| `/sucursal/{id}` | Sucursal | Resumen sucursal + bloques supervisores |
| `/mapa/{slug}` | Mapa | Mapa Leaflet con markers de clientes |

## Tests

```bash
# Backend (39 tests)
cd backend && .venv/bin/pytest -v

# Por archivo
.venv/bin/pytest tests/test_api.py -v
.venv/bin/pytest tests/test_ventas_service.py -v

# Por keyword
.venv/bin/pytest -k test_falta
```

## Stack Tecnico

### Backend
- **FastAPI** + Pydantic v2 (REST API + validacion)
- **Pandas** (procesamiento de datos)
- **psycopg2** (PostgreSQL)
- **Uvicorn** (ASGI server)

### Frontend
- **React 19** + TypeScript
- **Vite** (build tool + dev server con proxy)
- **Tailwind CSS v3** (mobile-first styling)
- **TanStack Query v5** (data fetching + cache)
- **React Router v7** (client-side routing)
- **Leaflet** (mapas OpenStreetMap)

### Bundle size
- JS: 446 KB (140 KB gzip)
- CSS: 28 KB (10 KB gzip)

## Reglas de Negocio

- **Tendencia** = ventas x (dias_habiles / dias_transcurridos)
- **% Tendencia** = tendencia / cupo x 100 (1 decimal)
- **Falta** = cupo - ventas
- Colores: verde >= 80%, amarillo 70-80%, rojo < 70%
- `TOTAL_CERVEZAS` es el cupo agregado de cervezas (no sumar marcas individuales)

## Base de Datos

PostgreSQL Gold layer (Medallion Architecture). Star schema con `fact_ventas` (7M+ filas). Ver `DB_CONTEXT_GOLD.md` para el esquema completo.

Requiere `.env` con `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`. Si la DB no esta disponible, el backend usa mock data automaticamente (excepto el endpoint de mapa).
