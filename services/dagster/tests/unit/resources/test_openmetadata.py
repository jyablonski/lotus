"""Tests for OpenMetadataResource."""

from unittest.mock import MagicMock, patch

from dagster import build_op_context
import pytest
import yaml

from dagster_project.resources import OpenMetadataResource


@pytest.mark.unit
class TestOpenMetadataResource:
    """Test the OpenMetadataResource."""

    def test_resource_initialization_defaults(self):
        resource = OpenMetadataResource(jwt_token="test-token")
        assert resource.host_port == "http://openmetadata_server:8585/api"
        assert resource.jwt_token == "test-token"

    @patch("dagster_project.resources.openmetadata.subprocess.run")
    def test_run_ingestion_success(self, mock_run):
        captured = {}

        def fake_run(command, **kwargs):
            config_path = command[5]
            captured["config_path"] = config_path
            with open(config_path) as f:
                captured["config"] = yaml.safe_load(f)
            return MagicMock(returncode=0, stdout="ok", stderr="")

        mock_run.side_effect = fake_run
        resource = OpenMetadataResource(jwt_token="test-token")
        context = build_op_context()

        resource.run_ingestion(
            context=context,
            source_config={"type": "postgres", "serviceName": "lotus_postgres"},
        )

        mock_run.assert_called_once()
        command = mock_run.call_args.args[0]
        assert command[:4] == [
            "/opt/om-ingestion/.venv/bin/python",
            "-m",
            "metadata",
            "ingest",
        ]
        assert command[4] == "-c"

        written_config = captured["config"]
        assert written_config["source"] == {
            "type": "postgres",
            "serviceName": "lotus_postgres",
        }
        assert written_config["sink"] == {"type": "metadata-rest", "config": {}}
        assert (
            written_config["workflowConfig"]["openMetadataServerConfig"]["hostPort"]
            == "http://openmetadata_server:8585/api"
        )
        assert (
            written_config["workflowConfig"]["openMetadataServerConfig"][
                "securityConfig"
            ]["jwtToken"]
            == "test-token"
        )

        # temp config file is cleaned up after the run
        import os

        assert not os.path.exists(captured["config_path"])

    @patch("dagster_project.resources.openmetadata.subprocess.run")
    def test_run_ingestion_raises_on_nonzero_exit(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="boom")
        resource = OpenMetadataResource(jwt_token="test-token")
        context = build_op_context()

        with pytest.raises(RuntimeError, match="exit 1"):
            resource.run_ingestion(context=context, source_config={"type": "postgres"})

    @patch("dagster_project.resources.openmetadata.subprocess.run")
    def test_run_script_command_shape(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        resource = OpenMetadataResource(jwt_token="test-token")
        context = build_op_context()

        resource.run_script(
            context=context,
            script_path="/app/src/dagster_project/openmetadata/sync_glossary.py",
            extra_args=[
                "--config",
                "/app/src/dagster_project/openmetadata/business_glossary.yaml",
            ],
        )

        mock_run.assert_called_once()
        command = mock_run.call_args.args[0]
        assert command == [
            "/opt/om-ingestion/.venv/bin/python",
            "/app/src/dagster_project/openmetadata/sync_glossary.py",
            "--host-port",
            "http://openmetadata_server:8585/api",
            "--jwt-token",
            "test-token",
            "--config",
            "/app/src/dagster_project/openmetadata/business_glossary.yaml",
        ]

    @patch("dagster_project.resources.openmetadata.subprocess.run")
    def test_run_script_raises_on_nonzero_exit(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="boom")
        resource = OpenMetadataResource(jwt_token="test-token")
        context = build_op_context()

        with pytest.raises(RuntimeError, match="exit 1"):
            resource.run_script(context=context, script_path="/some/script.py")
