from dagster import asset, AssetExecutionContext


@asset
def hello_world_asset(context: AssetExecutionContext) -> None:
    """Hello World asset."""
    context.log.info("Hello World v12345 boobs")
    return None
