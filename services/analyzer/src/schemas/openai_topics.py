from pydantic import BaseModel


class TopicAnalysis(BaseModel):
    topics: list[str]
    confidence_scores: list[float]


class AnalysisRequest(BaseModel):
    text: str
    max_topics: int = 5
    include_confidence: bool = True


class AnalysisResponse(BaseModel):
    analysis: TopicAnalysis
    metadata: dict
    processing_time_ms: float
