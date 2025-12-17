from dagster import define_asset_job, AssetSelection

hello_world_job = define_asset_job(
    name="hello_world_example_job",
    selection=AssetSelection.assets("hello_world_asset"),
)
