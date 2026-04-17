from dagster import AssetSelection, define_asset_job

llm_prompt_from_sheet_job = define_asset_job(
    name="llm_prompt_from_sheet_job",
    selection=AssetSelection.assets(
        "read_prompt_from_sheet", "run_prompt_and_write_result"
    ),
    tags={"audience": "internal", "domain": "ops", "pii": "false"},
    description=(
        "Read a stakeholder-authored prompt from Google Sheets, call OpenAI, "
        "and append the result to the Responses tab. Manual trigger only."
    ),
)
