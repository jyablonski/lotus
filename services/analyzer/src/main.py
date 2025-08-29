import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.dependencies import get_topic_client
from src.logger import setup_logging
from src.routers.v1 import v1_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Loading ML models...")
    topic_client = get_topic_client()
    topic_client.load_model()
    logger.info("ML models loaded successfully")

    yield

    # Shutdown (cleanup if needed)
    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)

app.include_router(v1_router, prefix="/v1")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    logger.info("Log test")
    return {"status": "healthy"}


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):  # noqa
    return JSONResponse(status_code=404, content={"detail": "this doesn't exist hoe"})
