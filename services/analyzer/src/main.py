from contextlib import asynccontextmanager
import logging
import os
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from opentelemetry import (
    metrics as otel_metrics,
    trace,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositeHTTPPropagator
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

from src.dependencies import get_sentiment_client, get_topic_client
from src.logger import setup_logging
from src.routers.v1 import v1_router

setup_logging()
logger = logging.getLogger(__name__)

_service_resource = Resource({"service.name": "lotus-analyzer"})


def _init_tracer() -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    provider = TracerProvider(resource=_service_resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces"))
    )
    trace.set_tracer_provider(provider)


def _init_meter() -> None:
    reader = PrometheusMetricReader()
    provider = MeterProvider(metric_readers=[reader], resource=_service_resource)
    otel_metrics.set_meter_provider(provider)


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
        logger.error(f"Failed to load ML models: {type(e).__name__}: {e}", exc_info=True)
        logger.error("Application will start but ML endpoints may fail")
        # Re-raise to prevent app from starting if models are critical
        # Comment out the next line if you want the app to start anyway
        raise

    # yield so app can run forever
    yield

    # Shutdown (cleanup if needed)
    logger.info("Shutting down...")


_init_tracer()
_init_meter()

# W3C TraceContext so incoming traceparent headers from the Go backend are
# extracted and the analyzer's spans appear as children in the same Jaeger trace.
set_global_textmap(CompositeHTTPPropagator([TraceContextTextMapPropagator()]))

app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)

_ANALYZER_API_KEY = os.getenv("ANALYZER_API_KEY", "")
if not _ANALYZER_API_KEY:
    raise RuntimeError("ANALYZER_API_KEY environment variable is required")

_UNPROTECTED_PATHS = {"/", "/health", "/metrics"}


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path in _UNPROTECTED_PATHS:
        return await call_next(request)
    expected = f"Bearer {_ANALYZER_API_KEY}"
    got = request.headers.get("Authorization", "")
    if not secrets.compare_digest(got, expected):
        return JSONResponse(status_code=401, content={"detail": "unauthorized"})
    return await call_next(request)


app.include_router(v1_router, prefix="/v1")


# can conditionally include routers depending on env vars

# if os.getenv("ENABLE_EXPERIMENTAL_ROUTER", "false").lower() == "true":
#     app.include_router(experimental_router, prefix="/experimental")


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    logger.info("Log test")
    return {"status": "healthy"}


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    detail = getattr(exc, "detail", "this doesn't exist hoe")
    return JSONResponse(status_code=404, content={"detail": detail})
