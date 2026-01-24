from dagster import ConfigurableResource, EnvVar
import requests


class ApiClientResource(ConfigurableResource):
    api_key: str
    base_url: str = ""

    def get_client(self) -> requests.Session:
        session = requests.Session()
        session.headers["Authorization"] = f"Bearer {self.api_key}"
        return session


api_client = ApiClientResource(
    api_key=EnvVar("API_KEY"),
    base_url=EnvVar("API_BASE_URL"),
)
