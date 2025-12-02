from app.domain.services.ml_handler.ml_handler import carregar_modelo_global
from contextlib import asynccontextmanager
from app.routers import api as api_router
from fastapi import FastAPI
from app.config.settings import get_settings
from app.config.logging import configure_logging
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure logging early
    configure_logging()

    # --- STARTUP ---
    logger.info("[Startup] Carregando modelo LSTM na memória...")

    caminho_modelo = settings.MODEL_PATH 

    modelo = carregar_modelo_global(caminho_modelo)

    app.state.model = modelo

    if modelo:
        logger.info("[Startup] Modelo carregado e pronto.")
    else:
        logger.error("[Startup] Falha ao carregar modelo.")

    yield 

app = FastAPI(lifespan=lifespan, title="Tech Challenge 4")

# Incluir rotas
app.include_router(api_router.router, prefix="/api", tags=["Predictions"])
