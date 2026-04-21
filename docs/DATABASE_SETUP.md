# Database Setup

## Architecture

The app uses two separate PostgreSQL databases:

| Database | Env prefix | Schema | Owner | Backup-critical |
|----------|-----------|--------|-------|----------------|
| `medallion_db` | `GOLD_DB_*` | `gold.*` | Gold/ETL team | No (regenerable from Silver) |
| `sellers_app_db` | `APP_DB_*` | `auth.*`, `operations.*` | App team | **YES** |

The backend has **read-only** access to `medallion_db` and **full** access to `sellers_app_db`.

## Local development setup

### 1. Create both databases

```bash
psql -U postgres -d postgres <<EOF
CREATE DATABASE medallion_db;   -- Gold DW (may already exist)
CREATE DATABASE sellers_app_db; -- App DB (new)
EOF
```

### 2. Run migrations on sellers_app_db

```bash
# From project root:
psql -U postgres -d sellers_app_db -f backend/migrations/001_auth_schema.sql
```

### 3. Configure .env

```
# Gold DW (medallion_db) — read-only
GOLD_DB_HOST=localhost
GOLD_DB_PORT=5432
GOLD_DB_NAME=medallion_db
GOLD_DB_USER=your_user
GOLD_DB_PASSWORD=your_password

# App DB (sellers_app_db) — read-write
APP_DB_HOST=localhost
APP_DB_PORT=5432
APP_DB_NAME=sellers_app_db
APP_DB_USER=your_user
APP_DB_PASSWORD=your_password
```

### 4. Seed admin user

```bash
cd backend
ADMIN_PASSWORD=changeme .venv/bin/python -m scripts.seed_admin
```

## Production setup

Same as dev, but use dedicated credentials and separate hosts if applicable.
See `DEPLOYMENT.md` for the full production runbook.

## Migrating from single-DB setup (legacy)

If you previously ran `001_auth_schema.sql` on `medallion_db` (the old single-DB setup):

1. Create `sellers_app_db` (step 1 above)
2. Run migrations on `sellers_app_db` (step 2 above)
3. Copy existing auth data:
   ```bash
   # Dump auth schema from old DB
   pg_dump -h $OLD_HOST -U $OLD_USER -d medallion_db \
     --schema=auth --data-only -f auth_data.sql

   # Restore into new DB
   psql -h $APP_DB_HOST -U $APP_DB_USER -d sellers_app_db -f auth_data.sql
   ```
4. Drop auth schema from medallion_db (optional cleanup):
   ```bash
   psql -h $GOLD_DB_HOST -U $GOLD_DB_USER -d medallion_db -c "DROP SCHEMA auth CASCADE;"
   ```
5. Update your `.env` to use `GOLD_DB_*` and `APP_DB_*` vars

## Module mapping

| File | Uses pool | DB |
|------|-----------|----|
| `data/gold_db.py` | Gold pool | `medallion_db` |
| `data/app_db.py` | App pool | `sellers_app_db` |
| `data/data_loader.py` | `gold_db` | Gold DW |
| `data/queries.py` | `gold_db` (via caller) | Gold DW |
| `routers/mapa.py` | `gold_db` | Gold DW |
| `auth/repository.py` | `app_db` | sellers_app_db |
| `auth/router.py` | `app_db` | sellers_app_db |
| `auth/admin_router.py` | `gold_db` (sucursales list) | medallion_db |
| `scripts/seed_admin.py` | direct psycopg2 | sellers_app_db |
