# Migración: Dash/Plotly → FastAPI + React

## Motivación
Dash tiene techo de escalabilidad: ~10 usuarios concurrentes, ~84 gráficos Plotly por page load (~5-12MB HTML/JSON), sin estado client-side, sin CRUD real, sin auth granular. La migración permite escalar a app web completa.

## Qué se conserva (728 líneas — backend puro Python)

### config.py (142 lín) — SIN CAMBIOS
- Mapeos de marcas, categorías, colores, nombres
- `get_dias_habiles()` con cache diario
- `color_por_rendimiento()` semáforo
- Todas las constantes de negocio

### src/data/db.py (45 lín) — REEMPLAZAR psycopg2 → asyncpg o SQLAlchemy async
- Pool de conexiones `SimpleConnectionPool(1-5)`
- `get_connection()` / `release_connection()`
- Credenciales via `.env`

### src/data/queries.py (73 lín) — CONSERVAR queries, adaptar ejecución
- `QUERY_VENTAS_MES` — ventas agregadas por vendedor/genérico/marca
- `QUERY_CLIENTES_VENDEDOR` — clientes con coordenadas para mapa
- Cambiar `pd.read_sql_query()` → ejecución async + retorno dicts

### src/data/data_loader.py (211 lín) — CONSERVAR lógica, adaptar cache
- Pipeline: BD → mapear categorías → CSV cupos → merge → derivadas
- Cache diario `get_dataframe()` / `_load_dataframe()`
- Fallback a mock_data si no hay BD
- Posible migración a Redis cache para compartir entre workers

### src/data/mock_data.py (121 lín) — SIN CAMBIOS
- 86 filas hardcodeadas, 10 vendedores, 2 supervisores
- Fallback para desarrollo sin BD

### src/services/ventas_service.py (136 lín) — SIN CAMBIOS (core del negocio)
- `calcular_tendencia(ventas)` → número
- `calcular_pct_tendencia(ventas, cupo)` → número
- `get_sucursales(df)` → [str]
- `get_supervisores(df, suc?)` → [str]
- `get_vendedores_por_supervisor(df, sup, suc?)` → [str]
- `get_datos_vendedor(df, v, cat)` → DataFrame
- `get_resumen_vendedor(df, v, cat)` → dict
- `get_datos_supervisor(df, sup, suc?, cat)` → DataFrame agregado
- `get_resumen_supervisor(df, sup, suc?, cat)` → dict
- `get_datos_sucursal(df, suc, cat)` → DataFrame agregado
- `get_resumen_sucursal(df, suc, cat)` → dict

## Qué se descarta (864 líneas — capa Dash)

| Archivo | Líneas | Razón |
|---------|--------|-------|
| src/app.py | 58 | Init Dash app → reemplaza FastAPI app |
| src/layouts/gauges.py | 145 | Plotly `go.Figure()` → React components |
| src/layouts/mapa.py | 51 | Plotly Scattermapbox → Leaflet/Mapbox GL |
| src/layouts/header.py | 49 | Dash HTML → React component |
| src/layouts/filters.py | 29 | `dcc.Dropdown` → React select |
| src/callbacks/views.py | 411 | Construcción de vistas → React pages |
| src/callbacks/dashboard_callbacks.py | 116 | Router + callbacks → React Router + API calls |
| run.py | 5 | `app.run()` → `uvicorn` |
| assets/styles.css | 720 | Migrar a Tailwind CSS |
| assets/carousel.js | 67 | Carrusel custom → librería React |

## Estructura propuesta del nuevo proyecto

```
seller-mobile-dashboard/
├── backend/                        # FastAPI (Python)
│   ├── main.py                     # App FastAPI + uvicorn
│   ├── config.py                   # ← config.py actual (sin cambios)
│   ├── .env                        # Variables de entorno
│   ├── requirements.txt
│   ├── data/
│   │   ├── db.py                   # ← adaptar a async (asyncpg)
│   │   ├── queries.py              # ← queries SQL intactas
│   │   ├── data_loader.py          # ← pipeline intacto
│   │   └── mock_data.py            # ← sin cambios
│   ├── services/
│   │   └── ventas_service.py       # ← sin cambios
│   ├── routers/
│   │   ├── dashboard.py            # Endpoints: sucursales, supervisores, vendedores
│   │   ├── mapa.py                 # Endpoint: clientes con coordenadas
│   │   └── health.py               # GET /health
│   ├── schemas/
│   │   └── models.py               # Pydantic models (response types)
│   └── tests/
│       └── ...                     # Migrar 26 tests existentes
│
├── frontend/                       # React (TypeScript)
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts              # Vite bundler
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx                 # React Router
│   │   ├── api/
│   │   │   └── client.ts           # Fetch wrapper → backend API
│   │   ├── components/
│   │   │   ├── GaugeTotal.tsx      # SVG gauge (reemplaza Plotly)
│   │   │   ├── RingMarca.tsx       # SVG ring por marca
│   │   │   ├── MapaClientes.tsx    # Leaflet/react-map-gl
│   │   │   ├── Header.tsx
│   │   │   ├── Filters.tsx         # Dropdowns sucursal + supervisor
│   │   │   ├── VendedorCard.tsx    # Bloque por vendedor
│   │   │   └── CategoryToggle.tsx  # Toggle CERVEZAS/MULTICCU/AGUAS
│   │   ├── pages/
│   │   │   ├── Home.tsx            # Vista principal (supervisor)
│   │   │   ├── Vendedor.tsx        # Detalle vendedor
│   │   │   ├── Supervisor.tsx      # Detalle supervisor
│   │   │   ├── Sucursal.tsx        # Vista sucursal
│   │   │   └── Mapa.tsx            # Mapa de clientes
│   │   ├── hooks/
│   │   │   ├── useVentas.ts        # React Query → API ventas
│   │   │   └── useFiltros.ts       # Estado de filtros
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript interfaces
│   │   └── styles/
│   │       └── globals.css         # Tailwind CSS
│   └── public/
│
├── data/                           # Archivos de datos (compartido)
│   ├── cupos.csv
│   ├── cupos_badie/
│   └── supervisores.xlsx
│
├── scripts/
│   └── procesar_cupos.py           # ← sin cambios
│
└── .claude/
    └── memory/
```

## Endpoints FastAPI propuestos

```
GET /health                                    → "ok"
GET /api/sucursales                            → [str]
GET /api/supervisores?sucursal={id}            → [str]
GET /api/vendedores?supervisor={sup}&sucursal={id}  → [str]

GET /api/dashboard?supervisor={sup}&sucursal={id}
  → {
      sucursal: { resumen, datos_por_marca[] },
      supervisor: { resumen, datos_por_marca[] },
      vendedores: [
        { nombre, resumen, datos_por_marca[] }
      ]
    }

GET /api/vendedor/{nombre}?categoria={cat}
  → { resumen, datos_por_marca[], categorias[] }

GET /api/supervisor/{nombre}?sucursal={id}&categoria={cat}
  → { resumen, datos_por_marca[], vendedores[] }

GET /api/sucursal/{id}?categoria={cat}
  → { resumen, datos_por_marca[] }

GET /api/mapa/{vendedor}?sucursal={id}
  → { clientes: [{ razon_social, fantasia, lat, lon, localidad }] }

GET /api/config/dias-habiles
  → { habiles, transcurridos, restantes, fecha }
```

## Stack frontend propuesto

| Necesidad | Dash actual | Propuesta React |
|-----------|-------------|-----------------|
| Bundler | N/A (server) | Vite |
| Routing | dcc.Location + callbacks | React Router v6 |
| Data fetching | Callbacks síncronos | TanStack Query (React Query) |
| Gauges | Plotly go.Indicator (~3MB) | SVG custom o Recharts (~200KB) |
| Mapa | Plotly Scattermapbox | react-leaflet o react-map-gl |
| CSS | Custom CSS 720 lín | Tailwind CSS |
| Dropdowns | dcc.Dropdown | Headless UI o Radix Select |
| Carrusel | JS custom 67 lín | Embla Carousel |
| Tipado | N/A | TypeScript |

## Orden de migración sugerido

### Fase 1: Backend FastAPI (sin tocar frontend Dash)
1. Crear `backend/main.py` con FastAPI
2. Mover config.py, data/, services/ al backend
3. Crear routers con endpoints REST
4. Crear schemas Pydantic
5. Migrar tests
6. Verificar que Dash sigue funcionando en paralelo

### Fase 2: Frontend React (mínimo viable)
1. Scaffolding: Vite + React + TypeScript + Tailwind
2. API client con TanStack Query
3. Componente GaugeTotal en SVG (reemplaza Plotly)
4. Componente RingMarca en SVG
5. Page Home con filtros + dashboard
6. Routing básico

### Fase 3: Paridad de features
1. Vista vendedor individual
2. Vista supervisor
3. Vista sucursal
4. Mapa de clientes (Leaflet)
5. Category toggle (CERVEZAS/MULTICCU/AGUAS)
6. Responsive mobile-first

### Fase 4: Features nuevas (imposibles en Dash)
- Autenticación (JWT)
- Roles (supervisor ve solo sus vendedores)
- PWA para mobile (offline capable)
- Notificaciones
- Comparación entre períodos
- Exportar a Excel/PDF

## Ganancia esperada

| Métrica | Dash actual | FastAPI + React |
|---------|-------------|-----------------|
| Payload home page | 5-12 MB | ~200 KB JSON + ~500 KB JS |
| Gráficos renderizados | 84 Plotly (server) | SVG client-side (lazy) |
| Usuarios concurrentes | 10-20 | 100+ |
| Time to interactive | 3-5s (mobile) | <1s |
| JS bundle | Plotly ~3MB | Recharts ~200KB |
| Features posibles | Solo lectura | CRUD, auth, PWA, real-time |
