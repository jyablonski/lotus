from fastapi import APIRouter

from .analyze import router as analyze_router
from .journal_sentiments import router as journal_sentiments_router
from .journal_topics import router as journal_topics_router

v1_router = APIRouter()

v1_router.include_router(analyze_router, tags=["analyze"])
v1_router.include_router(journal_topics_router, tags=["topics"])
v1_router.include_router(journal_sentiments_router, tags=["sentiments"])
