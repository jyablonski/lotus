from dagster import AssetExecutionContext, asset
import requests

from dagster_project.resources import ApiClientResource


@asset(group_name="ingestion")
def get_game_types_from_api(
    context: AssetExecutionContext, api_client: ApiClientResource
) -> list[dict]:
    """Fetch game types from API."""
    client = api_client.get_client()

    response = client.get("https://api.jyablonski.dev/v1/league/game_types")
    response.raise_for_status()
    context.log.info(f"Fetched {response.status_code} from API")

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        context.log.error(f"Failed to parse JSON: {response.text}")
        raise

    return data
