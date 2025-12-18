from dagster import AssetSelection, define_asset_job

unload_journal_entries_job = define_asset_job(
    name="unload_journal_entries_job",
    selection=AssetSelection.assets("unload_journals_to_s3"),
)
