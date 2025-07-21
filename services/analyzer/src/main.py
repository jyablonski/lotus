from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.logger import setup_logging
from src.routers.v1 import v1_router

setup_logging()

app = FastAPI()

app.include_router(v1_router, prefix="/v1")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):  # noqa
    return JSONResponse(status_code=404, content={"detail": "this doesn't exist hoe"})
