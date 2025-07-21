from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    sentiment_score: float
    mood_label: str
    keywords: list[str] | None = None
