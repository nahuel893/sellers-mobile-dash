"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from data.data_loader import get_dataframe

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm DataFrame cache al iniciar."""
    logger.info("Pre-warming DataFrame cache...")
    get_dataframe()
    logger.info("Cache ready.")
    yield


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
from routers.ventas_mapa import router as ventas_mapa_router
from routers.ventas_filtros import router as ventas_filtros_router
from routers.ventas_cliente import router as ventas_cliente_router
from auth.router import router as auth_router
from auth.admin_router import router as admin_router

app.include_router(dashboard_router)
app.include_router(mapa_router)
app.include_router(config_router)
app.include_router(cobertura_router)
app.include_router(ventas_mapa_router)
app.include_router(ventas_filtros_router)
app.include_router(ventas_cliente_router)
app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/health")
def health():
    return {"status": "ok"}
