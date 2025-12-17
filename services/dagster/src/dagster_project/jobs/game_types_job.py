from dagster import define_asset_job, AssetSelection

get_game_types_job = define_asset_job(
    name="get_game_types_job",
    selection=AssetSelection.assets("get_game_types_from_api"),
)
