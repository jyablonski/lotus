import os

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "default_key")
    mlflow_tracking_uri: str = os.getenv("MLFLOW_CONN_URI", "http://localhost:5000")
    environment: str = Field(default="dev", alias="ENV_TYPE")
    mlflow_experiment_name: str = "llm_topic_analysis"
    # default_model: str = "gpt-5-nano-2025-08-07"
    default_model: str = "gpt-4.1-nano"  # way more efficient
    max_tokens: int = 1000
    temperature: float = 0.1

    class Config:
        env_file = ".env"


settings = Settings()
