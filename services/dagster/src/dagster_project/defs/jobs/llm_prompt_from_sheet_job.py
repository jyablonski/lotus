from dagster_project.defs.assets.exports.llm_prompt_from_sheet import (
    read_prompt_from_sheet,
    run_prompt_and_write_result,
)
from dagster_project.defs.jobs.utils import Audience, Domain, create_job

llm_prompt_from_sheet_job = create_job(
    name="llm_prompt_from_sheet_job",
    assets=[read_prompt_from_sheet, run_prompt_and_write_result],
    audience=Audience.INTERNAL,
    domain=Domain.OPS,
    pii=False,
    description=(
        "Read a stakeholder-authored prompt from Google Sheets, call OpenAI, "
        "and append the result to the Responses tab. Manual trigger only."
    ),
)
