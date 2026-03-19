import logging
import time

import instructor
import mlflow
from openai import AsyncOpenAI
from pydantic import BaseModel, field_validator

from src.config import settings
from src.schemas.openai_topics import AnalysisRequest, TopicAnalysis

logger = logging.getLogger(__name__)


class OpenAITopicClient:
    """Topic extraction client backed by OpenAI via instructor structured outputs.

    Kept alongside the in-house semantic model so results can be compared
    directly. Both clients store results in the same journal_topics table,
    distinguished by ml_model_version.
    """

    def __init__(self) -> None:
        self.client = instructor.from_openai(AsyncOpenAI(api_key=settings.openai_api_key))
        self.model = settings.default_model

    async def analyze_topics(self, request: AnalysisRequest) -> TopicAnalysis:
        start_time = time.time()

        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment(settings.mlflow_experiment_name)

        with mlflow.start_run(run_name="openai_topic_analysis"):
            mlflow.log_params(
                {
                    "model": self.model,
                    "max_topics": request.max_topics,
                    "text_length": len(request.text),
                    "word_count": len(request.text.split()),
                }
            )

            max_topics = request.max_topics

            # Dynamic model enforces exact topic count at validation time.
            class DynamicTopicAnalysis(BaseModel):
                topics: list[str]
                confidence_scores: list[float]

                @field_validator("topics")
                @classmethod
                def validate_topic_count(cls, v: list[str]) -> list[str]:
                    if len(v) != max_topics:
                        raise ValueError(f"Must have exactly {max_topics} topics")
                    return v

                @field_validator("confidence_scores")
                @classmethod
                def validate_score_count(cls, v: list[float]) -> list[float]:
                    if len(v) != max_topics:
                        raise ValueError(f"Must have exactly {max_topics} confidence scores")
                    return v

            prompt = (
                f"Analyze the following journal entry and extract exactly "
                f"{max_topics} distinct topics that best represent its content. "
                f"For each topic provide a confidence score between 0 and 1.\n\n"
                f"Journal entry:\n{request.text}"
            )

            result: DynamicTopicAnalysis = await self.client.chat.completions.create(
                model=self.model,
                response_model=DynamicTopicAnalysis,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
            )

            processing_time_ms = (time.time() - start_time) * 1000
            logger.info(
                "OpenAI topic analysis complete in %.0f ms, model=%s",
                processing_time_ms,
                self.model,
            )

            if result.confidence_scores:
                mlflow.log_metrics(
                    {
                        "avg_confidence": sum(result.confidence_scores)
                        / len(result.confidence_scores),
                        "min_confidence": min(result.confidence_scores),
                        "max_confidence": max(result.confidence_scores),
                    }
                )

            return TopicAnalysis(
                topics=result.topics,
                confidence_scores=result.confidence_scores,
            )
