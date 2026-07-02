from pathlib import Path
import subprocess
import tempfile

from dagster import ConfigurableResource, EnvVar
import yaml

# Built by the `om-ingestion-deps` Docker stage into its own venv, isolated from
# the main project venv (openmetadata-ingestion's collate-sqllineage->sqlglot
# pin conflicts with dagster-dbt's, and it doesn't support this project's
# Python version). Invoked as `python -m metadata` rather than the `metadata`
# console script directly — that script's shebang bakes in the venv's build-time
# path, which breaks once the venv is copied to its final location.
OM_INGESTION_PYTHON = "/opt/om-ingestion/.venv/bin/python"


class OpenMetadataResource(ConfigurableResource):
    host_port: str = "http://openmetadata_server:8585/api"
    jwt_token: str

    def _run(self, *, context, command: list[str]) -> None:
        result = subprocess.run(command, capture_output=True, text=True)
        context.log.info(result.stdout)
        if result.returncode != 0:
            context.log.error(result.stderr)
            raise RuntimeError(
                f"OpenMetadata command failed (exit {result.returncode}): "
                f"{' '.join(command)}"
            )

    def run_ingestion(self, *, context, source_config: dict) -> None:
        """Run an OpenMetadata ingestion workflow in the isolated venv.

        `source_config` is the `source:` block (type/serviceName/sourceConfig);
        sink and workflowConfig are filled in here.
        """
        config = {
            "source": source_config,
            "sink": {"type": "metadata-rest", "config": {}},
            "workflowConfig": {
                "loggerLevel": "INFO",
                "openMetadataServerConfig": {
                    "hostPort": self.host_port,
                    "authProvider": "openmetadata",
                    "securityConfig": {"jwtToken": self.jwt_token},
                },
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(config, f)
            config_path = f.name

        try:
            self._run(
                context=context,
                command=[
                    OM_INGESTION_PYTHON,
                    "-m",
                    "metadata",
                    "ingest",
                    "-c",
                    config_path,
                ],
            )
        finally:
            Path(config_path).unlink(missing_ok=True)

    def run_script(
        self, *, context, script_path: str, extra_args: list[str] | None = None
    ) -> None:
        """Run a Python script in the isolated om-ingestion venv, passing this
        resource's connection config as --host-port/--jwt-token args."""
        self._run(
            context=context,
            command=[
                OM_INGESTION_PYTHON,
                script_path,
                "--host-port",
                self.host_port,
                "--jwt-token",
                self.jwt_token,
                *(extra_args or []),
            ],
        )


openmetadata_resource = OpenMetadataResource(
    host_port=EnvVar("OPENMETADATA_HOST_PORT"),
    jwt_token=EnvVar("OPENMETADATA_JWT_TOKEN"),
)
