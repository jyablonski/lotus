from dagster import define_asset_job, AssetSelection

unload_journal_entries_job = define_asset_job(
    name="unload_journal_entries_job",
    selection=AssetSelection.assets("unload_journals_to_s3"),
)
