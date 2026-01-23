from dagster import AssetSelection, define_asset_job

sync_flags_to_sheets_job = define_asset_job(
    name="sync_flags_to_sheets_job",
    selection=AssetSelection.assets(
        "get_feature_flags_from_postgres", "sync_flags_to_sheets"
    ),
    description="Sync feature flags from Postgres source.feature_flags table to Google Sheets",
)
