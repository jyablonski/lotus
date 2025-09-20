from fastapi import APIRouter

from .journal_sentiments import router as journal_sentiments_router
from .journal_topics import router as journal_topics_router
from .journal_topics_openai import router as journal_topics_openai_router

v1_router = APIRouter()

v1_router.include_router(journal_topics_router, tags=["topics"])
v1_router.include_router(journal_sentiments_router, tags=["sentiments"])
v1_router.include_router(journal_topics_openai_router, tags=["openai_topics"])
