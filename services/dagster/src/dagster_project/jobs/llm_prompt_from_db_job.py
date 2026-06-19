from dagster_project.assets.exports.llm_prompt_from_db import (
    read_sales_outreach_prompt,
    run_db_prompt_and_write_result,
)
from dagster_project.jobs.utils import Audience, Domain, create_job

llm_prompt_from_db_job = create_job(
    name="llm_prompt_from_db_job",
    assets=[read_sales_outreach_prompt, run_db_prompt_and_write_result],
    audience=Audience.INTERNAL,
    domain=Domain.OPS,
    pii=False,
    description=(
        "Read the sales_outreach prompt from stakeholder_prompts, call OpenAI, "
        "and persist the response to stakeholder_prompt_responses. "
        "Manual trigger only."
    ),
)
