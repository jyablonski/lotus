from fastapi import APIRouter

from .analyze import router as analyze_router

v1_router = APIRouter()

v1_router.include_router(analyze_router, tags=["analyze"])
