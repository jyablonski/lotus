from dagster import AssetSelection, define_asset_job

llm_prompt_from_db_job = define_asset_job(
    name="llm_prompt_from_db_job",
    selection=AssetSelection.assets(
        "read_sales_outreach_prompt", "run_db_prompt_and_write_result"
    ),
    tags={"audience": "internal", "domain": "ops", "pii": "false"},
    description=(
        "Read the sales_outreach prompt from stakeholder_prompts, call OpenAI, "
        "and persist the response to stakeholder_prompt_responses. "
        "Manual trigger only."
    ),
)
