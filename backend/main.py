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

app.include_router(dashboard_router)
app.include_router(mapa_router)
app.include_router(config_router)


@app.get("/health")
def health():
    return {"status": "ok"}
