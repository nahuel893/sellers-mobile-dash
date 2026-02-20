# Frontend — Avance Preventa

SPA React que consume la API FastAPI del backend.

## Stack

- **React 19** + TypeScript
- **Vite** (dev server con proxy a backend)
- **Tailwind CSS v3** (mobile-first)
- **TanStack Query v5** (data fetching + cache)
- **React Router v7** (client-side routing)
- **Leaflet** (mapas OpenStreetMap)

## Setup

```bash
npm install
npm run dev       # http://localhost:5173 (proxy /api → localhost:8000)
npm run build     # Produccion → dist/
npx tsc --noEmit  # Type check
```

Requiere el backend corriendo en `localhost:8000`.

## Estructura

```
src/
├── components/
│   ├── GaugeSvg.tsx          # SVG semicircular gauge (core)
│   ├── GaugeTotal.tsx        # Gauge grande + 4 metricas
│   ├── RingMarca.tsx         # Card marca con gauge chico
│   ├── CategorySlide.tsx     # Slide por categoria
│   ├── CategoryCarousel.tsx  # Scroll-snap horizontal + dots
│   ├── CategoryToggle.tsx    # Pills para sync global
│   ├── VendorIndex.tsx       # Quick-nav pills
│   ├── VendorBlock.tsx       # Bloque vendedor
│   ├── SummaryBlock.tsx      # Bloque sucursal/supervisor
│   ├── Header.tsx            # Header gradient + dias
│   ├── Filters.tsx           # Selects cascading
│   ├── BackLink.tsx          # Navegacion "< Volver"
│   └── CustomerMap.tsx       # Leaflet map wrapper
├── pages/
│   ├── HomePage.tsx          # Filtros + gauges + vendedores
│   ├── VendedorPage.tsx      # Categorias apiladas
│   ├── SupervisorPage.tsx    # Toggle + vendor blocks
│   ├── SucursalPage.tsx      # Sucursal + supervisores
│   ├── MapaPage.tsx          # Mapa de clientes
│   └── NotFoundPage.tsx      # 404
├── hooks/
│   ├── use-dashboard.ts      # Dashboard home
│   ├── use-dias-habiles.ts   # Dias habiles
│   ├── use-sucursales.ts     # Lista sucursales
│   ├── use-supervisores.ts   # Supervisores por sucursal
│   ├── use-vendedor.ts       # Detalle vendedor
│   ├── use-supervisor.ts     # Detalle supervisor
│   ├── use-sucursal.ts       # Detalle sucursal
│   └── use-mapa.ts           # Clientes para mapa
├── lib/
│   ├── api-client.ts         # Fetch wrapper tipado
│   ├── format.ts             # fmtNum, colorByPerformance, formatDateSpanish, toSlug
│   └── constants.ts          # Colores, categorias, marcas
├── types/
│   └── api.ts                # Interfaces 1:1 con backend/schemas.py
├── App.tsx                   # Router
├── main.tsx                  # React root + QueryClient + BrowserRouter
└── index.css                 # Tailwind + Inter font + carousel CSS + Leaflet
```

## Bundle

| Archivo | Size | Gzip |
|---------|------|------|
| JS | 446 KB | 140 KB |
| CSS | 28 KB | 10 KB |
