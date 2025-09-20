from pydantic import BaseModel, Field


class TopicAnalysis(BaseModel):
    topics: list[str] = Field(
        description="list of main topics found in the text", max_items=10
    )
    confidence_scores: list[float] = Field(
        description="Confidence score for each topic (0-1)", max_items=10
    )

    class Config:
        schema_extra = {
            "example": {
                "topics": ["machine learning", "data science", "AI ethics"],
                "confidence_scores": [0.95, 0.87, 0.73],
            }
        }


class AnalysisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000, description="Text to analyze")
    max_topics: int = Field(
        default=7, ge=1, le=20, description="Maximum number of topics to extract"
    )
    include_confidence: bool = Field(
        default=True, description="Include confidence scores"
    )


class AnalysisResponse(BaseModel):
    analysis: TopicAnalysis
    metadata: dict
    processing_time_ms: float
