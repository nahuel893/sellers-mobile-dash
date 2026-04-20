# Refactoring: De tablero a plataforma de tableros

## Objetivo

Convertir `seller-mobile-dashboard` en la plataforma web central que aloja N tableros, con autenticacion, RBAC y un home unificado. El unico tablero externo sera `sales-dashboard` (Dash/Python), integrado via proxy reverse.

## Estado actual

### seller-mobile-dashboard
- **Frontend**: React 19 + TypeScript + Vite + Tailwind + TanStack Query
- **Backend**: FastAPI + Pydantic v2 + Pandas
- **BD**: PostgreSQL (medallion_db, schema gold)
- **Auth**: Ninguna — API completamente publica
- **RBAC**: Ninguno
- **Deployment**: Solo script dev.sh (uvicorn + vite dev)
- **Tests**: 39 pytest (backend), sin tests frontend
- **Paginas**: Home, Vendedor, Supervisor, Sucursal, Mapa, Paneo

### sales-dashboard (tablero externo)
- **Stack**: Dash 4.0 + Plotly + dash-mantine-components
- **Auth**: Flask-Login + Flask-Session (activada via SECRET_KEY)
- **RBAC**: 3 roles (admin, gerente, supervisor) con filtro por sucursal
- **BD**: Misma PostgreSQL medallion_db
- **Puerto**: 8050
- **Tableros**: Ventas (mapas + comparativo), YTD, Detalle cliente, Busqueda clientes

## Arquitectura objetivo

```
seller-mobile-dashboard/          <- plataforma central
├── Auth (JWT + refresh tokens)
├── RBAC (roles + permisos)
├── Admin panel (gestion usuarios)
├── Home unificado (cards a cada tablero)
│
├── /sellers/*    -> tablero vendedores (ya existe, nativo)
├── /tablero-x/*  -> futuros tableros React (nativos)
│
└── /dash/*       -> proxy reverse a sales-dashboard:8050
                     (unico tablero externo)

sales-dashboard/                  <- satelite
├── Sin auth propio (confia en token del sistema central)
├── Middleware: valida JWT del header/cookie
└── Puerto 8050 (solo accesible desde proxy)
```

## Fases de implementacion

### Fase 1: Auth + RBAC en el backend FastAPI

**Objetivo**: Sistema de autenticacion JWT con roles.

**Tareas**:
- [ ] Modelo de usuario en PostgreSQL (tabla `auth.users`, `auth.roles`, `auth.user_sucursales`)
- [ ] Endpoints: `POST /api/auth/login`, `POST /api/auth/refresh`, `POST /api/auth/logout`
- [ ] JWT con access token (15 min) + refresh token (7 dias) + httpOnly cookies
- [ ] Middleware FastAPI (`Depends`) para proteger endpoints
- [ ] Roles: `admin`, `gerente`, `supervisor`, `vendedor`
- [ ] Filtro por sucursal segun rol (mismo patron que sales-dashboard: `get_user_sucursales()`)
- [ ] Seed script para crear usuario admin inicial
- [ ] Tests para auth endpoints y middleware

**Archivos nuevos**:
- `backend/auth/` (models, routes, dependencies, jwt)
- `backend/alembic/` o migration SQL

**Decisiones**:
- JWT (no sessions) — stateless, escala con multiples servicios
- Refresh token en httpOnly cookie — seguridad + UX
- Misma BD PostgreSQL, schema `auth` separado del `gold`

### Fase 2: Login + proteccion de rutas en el frontend React

**Objetivo**: Pantalla de login, contexto de usuario, rutas protegidas.

**Tareas**:
- [ ] Pagina `/login` con formulario (username + password)
- [ ] AuthContext/AuthProvider con estado del usuario + tokens
- [ ] Hook `useAuth()` para acceder al usuario y roles
- [ ] ProtectedRoute component (redirige a /login si no autenticado)
- [ ] RoleGuard component (redirige si el rol no tiene acceso)
- [ ] Interceptor en el API client para adjuntar JWT y manejar 401 (auto-refresh)
- [ ] Logout (limpiar tokens + redirigir)

**Archivos nuevos**:
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/components/ProtectedRoute.tsx`
- `frontend/src/components/RoleGuard.tsx`
- Modificar `frontend/src/lib/api.ts` (interceptor JWT)

### Fase 3: Home unificado

**Objetivo**: Landing page con cards a cada tablero disponible.

**Tareas**:
- [ ] Nueva pagina `/` con grid de cards (reemplaza el home actual)
- [ ] Card por tablero: icono, titulo, descripcion, link
- [ ] Tableros visibles segun rol del usuario
- [ ] Mover el home actual de vendedores a `/sellers` (o `/vendedores`)
- [ ] Actualizar rutas: todas las paginas actuales bajo prefijo `/sellers/*`

**Cards iniciales**:
- Vendedores (seller-mobile-dashboard nativo)
- Ventas (sales-dashboard via proxy)
- Futuro: agregar cards para nuevos tableros

**Archivos**:
- `frontend/src/pages/HomePage.tsx` (nuevo home con cards)
- `frontend/src/pages/sellers/` (mover paginas actuales aca)
- Actualizar `router` en App.tsx

### Fase 4: Integracion con sales-dashboard

**Objetivo**: Acceso al tablero Dash desde la plataforma central.

#### En seller-mobile-dashboard (plataforma):
- [ ] Ruta `/dash/*` en el frontend (componente con iframe o redirect)
- [ ] Configuracion Nginx: `location /dash/ { proxy_pass http://localhost:8050/; }`
- [ ] Pasar JWT al Dash via cookie compartida o query param seguro

#### En sales-dashboard (satelite):
- [ ] Reemplazar Flask-Login por middleware JWT simple
- [ ] Nuevo middleware: leer JWT del header/cookie, validar firma, extraer rol
- [ ] Eliminar login_layout.py, auth_callbacks.py, admin_layout.py (auth propia)
- [ ] Mantener RBAC por sucursal (get_user_sucursales basado en claims del JWT)
- [ ] Eliminar Flask-Session (stateless con JWT)

**Shared secret**: Ambos proyectos comparten la misma JWT_SECRET para validar tokens.

### Fase 5: Admin panel

**Objetivo**: Gestion de usuarios y roles desde la plataforma.

**Tareas**:
- [ ] Pagina `/admin/usuarios` (CRUD de usuarios)
- [ ] Asignacion de roles y sucursales
- [ ] Activar/desactivar usuarios
- [ ] Audit log (registro de acciones)
- [ ] Solo accesible para rol `admin`

**Nota**: Migrar la logica que ya existe en `sales-dashboard/callbacks/admin_callbacks.py` y `audit_callbacks.py` — no reescribir desde cero.

### Fase 6: Deployment

**Objetivo**: Llevar la plataforma a produccion.

**Tareas**:
- [ ] Dockerfile para backend (FastAPI + uvicorn)
- [ ] Dockerfile para frontend (build + nginx)
- [ ] docker-compose.yml (backend + frontend + redis)
- [ ] Nginx config: proxy a frontend, backend API, y sales-dashboard
- [ ] Configuracion de CORS y cookies cross-origin
- [ ] Variables de entorno para produccion (.env.production)
- [ ] Systemd service o docker-compose up en el servidor

## Consideraciones tecnicas

### JWT vs Sessions
Se elige JWT porque:
- Stateless — no necesita Redis para sesiones
- Escala a multiples servicios (Dash valida el mismo token)
- El refresh token en httpOnly cookie da seguridad similar a sessions

### Compartir auth con Dash
- **JWT_SECRET**: Variable compartida entre FastAPI y Dash
- **Validacion en Dash**: PyJWT (`import jwt`) para decodificar el token
- **Sin Flask-Login**: El middleware Dash solo necesita leer claims del JWT
- **Cookie compartida**: Misma domain, path `/`, httpOnly, secure

### Migracion de datos de usuarios
- Si ya hay usuarios en sales-dashboard (SQLite `auth.db`), migrarlos al PostgreSQL schema `auth`
- Passwords: bcrypt en ambos — compatibles directamente
- Roles: mapear admin/gerente/supervisor al nuevo sistema

### Rutas del tablero de vendedores
El home actual de seller-mobile-dashboard pasa a `/sellers`:
```
/                    -> Home unificado (cards)
/login               -> Login
/sellers             -> Home vendedores (ex /)
/sellers/vendedor/*  -> Detalle vendedor (ex /vendedor/*)
/sellers/supervisor/* -> Vista supervisor
/sellers/sucursal/*  -> Vista sucursal
/sellers/mapa/*      -> Mapa clientes
/sellers/paneo       -> Paneo automatico
/dash/ventas         -> Proxy a sales-dashboard
/dash/ytd            -> Proxy a sales-dashboard
/admin/usuarios      -> Admin panel
```

## Orden de ejecucion recomendado

```
Fase 1 (Auth backend)
  └─> Fase 2 (Auth frontend)
        └─> Fase 3 (Home unificado)
              ├─> Fase 4 (Integracion Dash) — puede ser paralela con Fase 5
              └─> Fase 5 (Admin panel)
                    └─> Fase 6 (Deployment)
```

## Esfuerzo estimado por fase

| Fase | Complejidad | Descripcion |
|------|-------------|-------------|
| 1 | Media | Auth JWT en FastAPI (modelos, endpoints, middleware) |
| 2 | Media | Login React + contexto + rutas protegidas |
| 3 | Baja | Reorganizar rutas + nuevo home con cards |
| 4 | Media | Proxy Nginx + refactor auth en sales-dashboard |
| 5 | Baja | Migrar admin panel existente de Dash a React |
| 6 | Media | Docker + Nginx + produccion |
