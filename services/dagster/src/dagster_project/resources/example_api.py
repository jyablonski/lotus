from datetime import UTC, datetime
from typing import Any

from dagster import ConfigurableResource, EnvVar
import requests


_FAKE_MODIFIED_RECORDS: list[dict[str, Any]] = [
    {
        "id": "example-001",
        "name": "Ada Lovelace",
        "status": "created",
        "modified_at": "2026-04-14T09:30:00+00:00",
    },
    {
        "id": "example-002",
        "name": "Grace Hopper",
        "status": "updated",
        "modified_at": "2026-04-15T15:45:00+00:00",
    },
    {
        "id": "example-003",
        "name": "Katherine Johnson",
        "status": "created",
        "modified_at": "2026-04-16T22:10:00+00:00",
    },
    {
        "id": "example-004",
        "name": "Mary Jackson",
        "status": "updated",
        "modified_at": "2026-04-17T06:20:00+00:00",
    },
    {
        "id": "example-005",
        "name": "Dorothy Vaughan",
        "status": "created",
        "modified_at": "2026-04-18T04:05:00+00:00",
    },
]


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


class ApiClientResource(ConfigurableResource):
    api_key: str
    base_url: str = ""

    def get_client(self) -> requests.Session:
        session = requests.Session()
        session.headers["Authorization"] = f"Bearer {self.api_key}"
        return session

    def fetch_modified_records(
        self,
        *,
        modified_at_gte: datetime,
        modified_at_lt: datetime,
        page_token: str | None = None,
        page_size: int = 100,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of records modified inside [gte, lt).

        When API_BASE_URL is blank, this returns deterministic in-process sample data.
        When API_BASE_URL is set, it calls ``{base_url}/records`` with common
        incremental API query parameters.
        """
        if self.base_url:
            return self._fetch_remote_modified_records(
                modified_at_gte=modified_at_gte,
                modified_at_lt=modified_at_lt,
                page_token=page_token,
                page_size=page_size,
            )

        return self._fetch_fake_modified_records(
            modified_at_gte=modified_at_gte,
            modified_at_lt=modified_at_lt,
            page_token=page_token,
            page_size=page_size,
        )

    def _fetch_remote_modified_records(
        self,
        *,
        modified_at_gte: datetime,
        modified_at_lt: datetime,
        page_token: str | None,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], str | None]:
        client = self.get_client()
        params: dict[str, str | int] = {
            "modified_at_gte": modified_at_gte.isoformat(),
            "modified_at_lt": modified_at_lt.isoformat(),
            "page_size": page_size,
        }
        if page_token is not None:
            params["page_token"] = page_token

        response = client.get(f"{self.base_url.rstrip('/')}/records", params=params)
        response.raise_for_status()
        payload = response.json()

        if isinstance(payload, list):
            return payload, None

        records = payload.get("records", payload.get("data", []))
        next_page_token = payload.get("next_page_token")
        return records, next_page_token

    def _fetch_fake_modified_records(
        self,
        *,
        modified_at_gte: datetime,
        modified_at_lt: datetime,
        page_token: str | None,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], str | None]:
        lower_bound = modified_at_gte.astimezone(UTC)
        upper_bound = modified_at_lt.astimezone(UTC)
        filtered_records = [
            dict(record)
            for record in _FAKE_MODIFIED_RECORDS
            if lower_bound <= _parse_datetime(record["modified_at"]) < upper_bound
        ]
        filtered_records.sort(key=lambda record: (record["modified_at"], record["id"]))

        start = int(page_token or 0)
        end = start + page_size
        next_page_token = str(end) if end < len(filtered_records) else None
        return filtered_records[start:end], next_page_token


api_client = ApiClientResource(
    api_key=EnvVar("API_KEY"),
    base_url=EnvVar("API_BASE_URL"),
)
