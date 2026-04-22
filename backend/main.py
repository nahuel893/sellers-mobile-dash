"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from data.data_loader import get_dataframe

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm DataFrame cache y pools de conexiones al iniciar."""
    # Inicializar pool Gold DB (medallion_db)
    try:
        from data import gold_db
        gold_db.init_pool()
        logger.info("Gold DB pool (medallion_db) listo.")
    except Exception as exc:
        logger.warning("Gold DB pool no se pudo inicializar: %s", exc)

    # Inicializar pool App DB (sellers_app_db)
    try:
        from data import app_db
        app_db.init_pool()
        logger.info("App DB pool (sellers_app_db) listo.")
    except Exception as exc:
        logger.warning("App DB pool no se pudo inicializar: %s", exc)

    # Pre-warm DataFrame cache (usa Gold DB)
    logger.info("Pre-warming DataFrame cache...")
    get_dataframe()
    logger.info("Cache listo.")

    yield

    # Cerrar ambos pools al apagar
    try:
        from data import gold_db
        gold_db.close_pool()
    except Exception as exc:
        logger.warning("Error cerrando Gold DB pool: %s", exc)

    try:
        from data import app_db
        app_db.close_pool()
    except Exception as exc:
        logger.warning("Error cerrando App DB pool: %s", exc)


app = FastAPI(
    title="Seller Mobile Dashboard API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - permitir React dev server y producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
from routers.dashboard import router as dashboard_router
from routers.mapa import router as mapa_router
from routers.config_router import router as config_router
from routers.cobertura import router as cobertura_router
from routers.preventistas import router as preventistas_router
from routers.avance import router as avance_router
from routers.weather import router as weather_router
from auth.router import router as auth_router
from auth.admin_router import router as admin_router

app.include_router(dashboard_router)
app.include_router(mapa_router)
app.include_router(config_router)
app.include_router(cobertura_router)
app.include_router(preventistas_router)
app.include_router(avance_router)
app.include_router(weather_router)
app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/health")
def health():
    return {"status": "ok"}
