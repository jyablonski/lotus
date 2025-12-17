import os
import requests
from dagster import ConfigurableResource


class ApiClientResource(ConfigurableResource):
    api_key: str
    base_url: str = ""

    def get_client(self) -> requests.Session:
        session = requests.Session()
        session.headers["Authorization"] = f"Bearer {self.api_key}"
        return session


api_client = ApiClientResource(
    api_key=os.getenv("API_KEY", ""),
    base_url=os.getenv("API_BASE_URL", ""),
)
