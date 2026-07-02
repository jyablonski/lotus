from dagster import build_op_context
import pytest

from dagster_project.defs.assets.catalog.openmetadata_glossary_sync import (
    openmetadata_glossary_sync,
)
from dagster_project.openmetadata import BUSINESS_GLOSSARY_YAML, SYNC_SCRIPT_PATH


class FakeOpenMetadataResource:
    def __init__(self):
        self.calls = []

    def run_script(self, *, context, script_path, extra_args=None):
        self.calls.append((script_path, extra_args))


@pytest.mark.unit
class TestOpenmetadataGlossarySync:
    def test_runs_sync_script_against_business_glossary_yaml(self):
        context = build_op_context()
        fake_resource = FakeOpenMetadataResource()

        openmetadata_glossary_sync(context, openmetadata_resource=fake_resource)

        assert len(fake_resource.calls) == 1
        script_path, extra_args = fake_resource.calls[0]
        assert script_path == str(SYNC_SCRIPT_PATH)
        assert extra_args == ["--config", str(BUSINESS_GLOSSARY_YAML)]
