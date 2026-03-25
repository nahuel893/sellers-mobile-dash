# Seller Mobile Dashboard - Contexto del Proyecto

## Qué es
Dashboard mobile-first (Dash/Plotly) para preventistas de cervecería. Muestra avance de ventas vs cupo por grupo de marca con % en **tendencia** (proyección a fin de mes).

## Arquitectura
- **Capas**: data → services → layouts + callbacks/views (separación de responsabilidades)
- **Entry point**: `run.py` → `src/app.py`
- **Stack**: Dash + dash-bootstrap-components + Plotly + Pandas + psycopg2 + python-dotenv
- **BD**: PostgreSQL capa Gold (Medallion architecture) - ver `DB_CONTEXT_GOLD.md`
- **Datos**: ventas reales de PostgreSQL + cupos de CSV (fallback a mock_data si no hay BD)
- **Data refresh**: `get_dataframe()` cachea por día, recarga automáticamente al cambiar fecha
- **Layout dinámico**: `app.layout = serve_layout` (función), header se re-evalúa por request
- **Connection pooling**: `psycopg2.pool.SimpleConnectionPool` (1-5 conns) en `db.py`
- **Despliegue previsto**: Gunicorn en Debian 13 local + instancia cloud via VPN a BD local

## Estructura de archivos
```
run.py, config.py, requirements.txt, .env.example, .env (gitignored)
src/app.py                          # Init Dash, serve_layout (función), pre-warm cache, /health
src/data/db.py                      # Pool conexiones PostgreSQL (SimpleConnectionPool)
src/data/queries.py                 # Queries SQL: ventas mes + clientes vendedor
src/data/data_loader.py             # Orquestador: BD ventas + CSV cupos → DataFrame (cache diario)
src/data/mock_data.py               # Datos mock (fallback), usa _calcular_columnas_derivadas
src/services/ventas_service.py      # Cálculos: tendencia, pct, filtros, agregaciones por jerarquía
src/layouts/header.py               # Header con fecha dinámica + días hábiles (sin locale)
src/layouts/filters.py              # Dropdowns sucursal + supervisor
src/layouts/gauges.py               # Gauge total + ring marca (Plotly Indicator)
src/layouts/mapa.py                 # Mapa Scattermapbox de clientes por vendedor
src/callbacks/dashboard_callbacks.py # Router + callbacks (115 líneas, slim)
src/callbacks/views.py              # Funciones de construcción de vistas (411 líneas)
assets/styles.css                   # CSS responsive + carrusel scroll-snap + sidebar sticky
assets/carousel.js                  # JS dots tracking + click navigation
data/cupos.csv                      # Cupos por vendedor+sucursal (generado desde Excel)
data/cupos_badie/                   # Excel originales de cupos (3 archivos)
data/supervisores.xlsx              # Jerarquía vendedor→supervisor (solo Casa Central)
scripts/procesar_cupos.py           # Excel → cupos.csv (cruza con dim_cliente + supervisores)
tests/                              # 26 tests pytest
```

## Routing (multi-URL con slugs)
- `dcc.Location` + callback router en `dashboard_callbacks.py`
- `suppress_callback_exceptions=True` en app (layout dinámico)
- Helpers en `views.py`: `to_slug(nombre)`, `from_slug(slug)`, `find_sucursal(df, id)`
- Slugs codifican guiones literales como %2D para reversibilidad
- Rutas: `/` home, `/vendedor/SLUG`, `/supervisor/SLUG?sucursal=ID`, `/sucursal/ID`, `/mapa/SLUG?sucursal=ID`, `/health`
- Cada vista directa tiene "< Volver" link
- Índice de vendedores con botón "Inicio" (scroll-to-top)

## Reglas de negocio clave
- **Tendencia** = ventas * (dias_habiles / dias_transcurridos) — SIN redondeo
- **% Tendencia** = tendencia / cupo * 100 — SIN redondeo, display con 1 decimal
- **Falta** = cupo - ventas
- Semáforo: verde >=80%, amarillo 70-80%, rojo <70%
- Días hábiles: `get_dias_habiles()` en config.py (cache diario, auto-refresh)
- DIAS_TRANSCURRIDOS y DIAS_RESTANTES tienen mínimo 1 (evita division by zero)
- Fecha del header formateada con arrays de nombres en español (sin locale)

## Mapeos de marcas (config.py)
- **MAPEO_MARCA_GRUPO**: dim_articulo.marca → grupo_marca
  - NORTE → SALTA (TODO: revisar, confirmado solo para Güemes)
  - SALTA CAUTIVA1 → independiente (suma al total cervezas, sin gauge propio)
  - SCHNEIDER, AMSTEL, WARSTEINER, GROLSCH, BIECKERT, ISENBECK, IGUANA → MULTICERVEZAS
  - SOL, BLUE MOON, KUNSTMAN/KUNSTMANN → IMPORTADAS
- **MAPEO_DESAGREGADO_CUPO**: Excel DESAGREGADO → (categoria, grupo_marca)
  - CERVEZAS → ('CERVEZAS', 'TOTAL_CERVEZAS') — usar este cupo para total, no sumar individuales

## Data Loader - Merge y Cache
- OUTER merge ventas BD + cupos CSV on [vendedor, sucursal, categoria, grupo_marca]
- Sentinel `__NONE__` para grupo_marca=None (NaN != NaN en pandas merge)
- TOTAL_CERVEZAS: separado del merge, agregado después con ventas=0
- `get_dataframe()` cachea por fecha, `_load_dataframe()` hace la carga real
- Supervisor lookup: merge vectorizado (no apply/lambda)
- Error handling: `_EXPECTED_ERRORS` para fallback a mock, re-raise en bugs

## BD Gold - Tablas principales
- `fact_ventas`: `cantidades_total`, `subtotal_final`
- `dim_articulo`: `marca`, `generico`
- `dim_vendedor`: FV1=Preventa. Clave: (id_vendedor + id_sucursal)
- `dim_cliente`: `id_ruta_fv1`, `des_personal_fv1`, `latitud`, `longitud`, `fantasia`, `razon_social`, `des_localidad`, `anulado`. Clave: (id_cliente + id_sucursal)
- `dim_sucursal`: columna es `descripcion` (NO `des_sucursal`)

## Issues conocidos
- `responsive=True` en dcc.Graph rompe gauges - NO usar
- README.md tiene corrupción - no commitear sin limpiar
- `NORMALIZAR_VENDEDOR` y `VENDEDORES_EXCLUIR` solo en scripts, no runtime
- Demasiados graphs Plotly en home page (candidato a lazy loading futuro)
