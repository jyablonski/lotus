import time

import instructor
import mlflow
from openai import OpenAI
from pydantic import Field

from src.config import settings
from src.schemas.openai_topics import AnalysisRequest, TopicAnalysis


class OpenAITopicClient:
    def __init__(self):
        self.client = instructor.from_openai(OpenAI(api_key=settings.openai_api_key))
        self._setup_mlflow()

    def _setup_mlflow(self):
        """Initialize MLflow tracking"""
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)

        try:
            experiment = mlflow.get_experiment_by_name(settings.mlflow_experiment_name)
            if experiment is None:
                mlflow.create_experiment(settings.mlflow_experiment_name)
        except Exception:
            mlflow.create_experiment(settings.mlflow_experiment_name)

        mlflow.set_experiment(settings.mlflow_experiment_name)

    async def analyze_topics(self, request: AnalysisRequest) -> TopicAnalysis:
        """Extract topics using Instructor + OpenAI with MLflow tracking"""

        with mlflow.start_run(run_name=f"topic_analysis_{int(time.time())}"):
            start_time = time.time()

            # Log input parameters
            mlflow.log_params(
                {
                    "model": settings.default_model,
                    "max_topics": request.max_topics,
                    "temperature": settings.temperature,
                    "text_length": len(request.text),
                    "word_count": len(request.text.split()),
                }
            )

            description = (
                f"Confidence score for each of the {request.max_topics} topics"
            )

            # Create dynamic response model based on max_topics
            class DynamicTopicAnalysis(TopicAnalysis):
                topics: list[str] = Field(
                    description=f"Exactly {request.max_topics} main topics",
                    min_items=request.max_topics,
                    max_items=request.max_topics,
                )
                confidence_scores: list[float] = Field(description=description)

            try:
                system_prompt = (
                    "You are an expert text analyst. Extract exactly "
                    f"{request.max_topics} most relevant topics from the given text. "
                    "Rank them by importance and assign confidence scores (0-1)."
                )

                user_prompt = (
                    f"Analyze this text and extract the top {request.max_topics} "
                    f"topics:\n\n{request.text}"
                )

                # Make the API call with Instructor
                response = self.client.chat.completions.create(
                    model=settings.default_model,
                    response_model=DynamicTopicAnalysis,
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )

                processing_time = (time.time() - start_time) * 1000

                # Log metrics
                mlflow.log_metrics(
                    {
                        "processing_time_ms": processing_time,
                        "avg_confidence": sum(response.confidence_scores)
                        / len(response.confidence_scores),
                        "min_confidence": min(response.confidence_scores),
                        "max_confidence": max(response.confidence_scores),
                    }
                )

                # Log outputs
                mlflow.log_dict(
                    {
                        "topics": response.topics,
                        "confidence_scores": response.confidence_scores,
                        "main_theme": response.main_theme,
                    },
                    "analysis_output.json",
                )

                # Log the prompt for reproducibility
                mlflow.log_text(
                    request.text[:500] + "..."
                    if len(request.text) > 500
                    else request.text,
                    "input_text_sample.txt",
                )

                return response

            except Exception as e:
                mlflow.log_param("error", str(e))
                raise e
