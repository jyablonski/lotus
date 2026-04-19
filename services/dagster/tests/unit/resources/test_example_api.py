from datetime import UTC, datetime

import pytest

from dagster_project.resources.example_api import ApiClientResource


@pytest.mark.unit
class TestApiClientResource:
    def test_fetch_modified_records_uses_fake_data_when_base_url_is_blank(self):
        api_client = ApiClientResource(api_key="test-key", base_url="")

        records, next_page_token = api_client.fetch_modified_records(
            modified_at_gte=datetime(2026, 4, 15, 0, 0, tzinfo=UTC),
            modified_at_lt=datetime(2026, 4, 18, 0, 0, tzinfo=UTC),
            page_size=2,
        )

        assert [record["id"] for record in records] == ["example-002", "example-003"]
        assert next_page_token == "2"

        records, next_page_token = api_client.fetch_modified_records(
            modified_at_gte=datetime(2026, 4, 15, 0, 0, tzinfo=UTC),
            modified_at_lt=datetime(2026, 4, 18, 0, 0, tzinfo=UTC),
            page_token=next_page_token,
            page_size=2,
        )

        assert [record["id"] for record in records] == ["example-004"]
        assert next_page_token is None
