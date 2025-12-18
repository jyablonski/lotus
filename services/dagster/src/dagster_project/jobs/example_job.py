from dagster import AssetSelection, define_asset_job

hello_world_job = define_asset_job(
    name="hello_world_example_job",
    selection=AssetSelection.assets("hello_world_asset"),
)
