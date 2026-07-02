from dagster import build_op_context
import pytest

from dagster_project.defs.assets.catalog import openmetadata_sync as sync_module
from dagster_project.defs.assets.catalog.openmetadata_sync import (
    POSTGRES_SERVICE_NAME,
    openmetadata_dbt_sync,
    openmetadata_postgres_sync,
)


class FakeOpenMetadataResource:
    def __init__(self):
        self.calls = []

    def run_ingestion(self, *, context, source_config):
        self.calls.append(source_config)


@pytest.mark.unit
class TestOpenmetadataPostgresSync:
    def test_ingests_source_silver_gold_schemas(self):
        context = build_op_context()
        fake_resource = FakeOpenMetadataResource()

        openmetadata_postgres_sync(context, openmetadata_resource=fake_resource)

        assert len(fake_resource.calls) == 1
        source_config = fake_resource.calls[0]
        assert source_config["type"] == "postgres"
        assert source_config["serviceName"] == POSTGRES_SERVICE_NAME
        assert source_config["sourceConfig"]["config"]["schemaFilterPattern"][
            "includes"
        ] == ["source", "silver", "gold"]


@pytest.mark.unit
class TestOpenmetadataDbtSync:
    def test_uses_manifest_and_run_results_from_dbt_target(self, monkeypatch):
        monkeypatch.setattr(sync_module, "dbt_project", object())
        context = build_op_context()
        fake_resource = FakeOpenMetadataResource()

        openmetadata_dbt_sync(context, openmetadata_resource=fake_resource)

        assert len(fake_resource.calls) == 1
        source_config = fake_resource.calls[0]
        assert source_config["type"] == "dbt"
        assert source_config["serviceName"] == POSTGRES_SERVICE_NAME
        dbt_config_source = source_config["sourceConfig"]["config"]["dbtConfigSource"]
        assert dbt_config_source["dbtConfigType"] == "local"
        assert dbt_config_source["dbtManifestFilePath"].endswith(
            "dbt/target/manifest.json"
        )
        assert dbt_config_source["dbtRunResultsFilePath"].endswith(
            "dbt/target/run_results.json"
        )

    def test_skips_when_dbt_project_unavailable(self, monkeypatch):
        monkeypatch.setattr(sync_module, "dbt_project", None)
        context = build_op_context()
        fake_resource = FakeOpenMetadataResource()

        openmetadata_dbt_sync(context, openmetadata_resource=fake_resource)

        assert fake_resource.calls == []
