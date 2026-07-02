from dagster import AssetExecutionContext, asset

from dagster_project.openmetadata import BUSINESS_GLOSSARY_YAML, SYNC_SCRIPT_PATH
from dagster_project.resources.openmetadata import OpenMetadataResource


@asset(group_name="catalog")
def openmetadata_glossary_sync(
    context: AssetExecutionContext, openmetadata_resource: OpenMetadataResource
) -> None:
    """Apply dagster_project/openmetadata/business_glossary.yaml to OpenMetadata —
    idempotent upsert, safe to re-run after editing the YAML."""
    openmetadata_resource.run_script(
        context=context,
        script_path=str(SYNC_SCRIPT_PATH),
        extra_args=["--config", str(BUSINESS_GLOSSARY_YAML)],
    )
