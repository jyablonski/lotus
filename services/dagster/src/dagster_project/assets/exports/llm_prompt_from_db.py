"""Read a stakeholder-authored prompt from the ``stakeholder_prompts`` table,
call OpenAI, and persist the result to ``stakeholder_prompt_responses``.

The ``application`` column on ``stakeholder_prompts`` identifies what the
prompt is used for (e.g. ``sales_outreach``). Each Dagster job is hard-coded
to a single ``application`` value, so stakeholders can freely edit the prompt
text in the Django admin without changing code.

The ``run_prompt_from_db`` helper below is the reusable core. To add another
prompt-driven job backed by the database:

1. Add a new row to ``stakeholder_prompts`` (via Django migration or admin)
   with a new ``application`` value.
2. Write a new asset that injects ``postgres_conn`` + ``openai_client`` and
   calls ``run_prompt_from_db(...)`` with your ``application`` value.
3. Wire it up in a ``define_asset_job`` under ``jobs/``.
"""

from dagster import AssetExecutionContext, asset

from dagster_project.resources import OpenAIResource, PostgresResource
from dagster_project.sql.exports import (
    INSERT_STAKEHOLDER_PROMPT_RESPONSE,
    SELECT_STAKEHOLDER_PROMPT_BY_APPLICATION,
)

SALES_OUTREACH_APPLICATION = "sales_outreach"


def fetch_stakeholder_prompt(postgres: PostgresResource, application: str) -> dict:
    """Return the row for ``application`` as ``{id, stakeholder_group, application, prompt}``.

    Raises ``ValueError`` if no matching row exists.
    """
    with postgres.get_connection() as conn, conn.cursor() as cur:
        cur.execute(SELECT_STAKEHOLDER_PROMPT_BY_APPLICATION, (application,))
        row = cur.fetchone()

    if row is None:
        raise ValueError(
            f"No stakeholder_prompts row found for application={application!r}"
        )

    prompt_id, stakeholder_group, application_val, prompt_text = row
    return {
        "id": str(prompt_id),
        "stakeholder_group": stakeholder_group,
        "application": application_val,
        "prompt": prompt_text,
    }


def write_stakeholder_prompt_response(
    postgres: PostgresResource,
    stakeholder_prompt_id: str,
    model: str,
    response: str,
) -> None:
    """Insert a row into ``stakeholder_prompt_responses``."""
    with postgres.get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            INSERT_STAKEHOLDER_PROMPT_RESPONSE,
            (stakeholder_prompt_id, model, response),
        )
        conn.commit()


def run_prompt_from_db(
    *,
    postgres: PostgresResource,
    openai: OpenAIResource,
    application: str,
    model: str | None = None,
    system: str | None = None,
) -> dict:
    """Look up the prompt for ``application``, call OpenAI, persist the response.

    Returns a dict with keys ``stakeholder_prompt_id``, ``application``,
    ``prompt``, ``model``, ``response``.
    """
    prompt_row = fetch_stakeholder_prompt(postgres, application)
    if not prompt_row["prompt"]:
        raise ValueError(
            f"stakeholder_prompts row for application={application!r} has an empty prompt"
        )

    response = openai.complete(prompt_row["prompt"], model=model, system=system)
    effective_model = model or openai.default_model

    write_stakeholder_prompt_response(
        postgres=postgres,
        stakeholder_prompt_id=prompt_row["id"],
        model=effective_model,
        response=response,
    )

    return {
        "stakeholder_prompt_id": prompt_row["id"],
        "application": prompt_row["application"],
        "prompt": prompt_row["prompt"],
        "model": effective_model,
        "response": response,
    }


@asset(group_name="exports")
def read_sales_outreach_prompt(
    context: AssetExecutionContext,
    postgres_conn: PostgresResource,
) -> dict:
    """Load the ``sales_outreach`` stakeholder prompt row from Postgres."""
    row = fetch_stakeholder_prompt(postgres_conn, SALES_OUTREACH_APPLICATION)
    context.add_output_metadata(
        {
            "application": row["application"],
            "stakeholder_group": row["stakeholder_group"],
            "prompt_preview": row["prompt"][:200],
        }
    )
    return row


@asset(group_name="exports")
def run_db_prompt_and_write_result(
    context: AssetExecutionContext,
    read_sales_outreach_prompt: dict,
    postgres_conn: PostgresResource,
    openai_client: OpenAIResource,
) -> None:
    """Run the sales_outreach prompt through OpenAI and persist the response."""
    del read_sales_outreach_prompt  # dependency only; runner re-fetches to stay atomic

    result = run_prompt_from_db(
        postgres=postgres_conn,
        openai=openai_client,
        application=SALES_OUTREACH_APPLICATION,
    )

    context.log.info(
        f"Wrote response ({len(result['response'])} chars) for "
        f"application={result['application']} using model {result['model']}"
    )
    context.add_output_metadata(
        {
            "application": result["application"],
            "model": result["model"],
            "response_preview": result["response"][:200],
        }
    )
