from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.dependencies import get_sentiment_client, get_topic_client
from src.logger import setup_logging
from src.routers.v1 import v1_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Loading ML models...")
    try:
        topic_client = get_topic_client()
        topic_client.load_model()
        logger.info("Topic model loaded successfully")

        sentiment_client = get_sentiment_client()
        sentiment_client.load_model()
        logger.info("Sentiment model loaded successfully")
        logger.info("All ML models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load ML models: {e}")
        logger.error("Application will start but ML endpoints may fail")
        # Re-raise to prevent app from starting if models are critical
        # Comment out the next line if you want the app to start anyway
        raise

    # yield so app can run forever
    yield

    # Shutdown (cleanup if needed)
    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)

app.include_router(v1_router, prefix="/v1")


# can conditionally include routers depending on env vars

# if os.getenv("ENABLE_EXPERIMENTAL_ROUTER", "false").lower() == "true":
#     app.include_router(experimental_router, prefix="/experimental")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    logger.info("Log test")
    return {"status": "healthy"}


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "this doesn't exist hoe"})
