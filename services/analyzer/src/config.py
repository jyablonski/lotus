import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow_experiment_name: str = "llm_topic_analysis"
    default_model: str = "gpt-5-nano"
    max_tokens: int = 1000
    temperature: float = 0.1

    class Config:
        env_file = ".env"


settings = Settings()
