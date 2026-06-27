"""Read a stakeholder-authored prompt from a Google Sheet, call OpenAI, and
append the result to a separate tab in the same sheet.

Sheet layout (this job):
- Tab ``Prompt``: ``B1`` holds the editable prompt text, ``B2`` optionally holds
  a model override (falls back to ``OpenAIResource.default_model``).
- Tab ``Responses``: auto-created on first run. Columns: ``run_at, prompt,
  model, response``. One row appended per run.

The ``run_prompt_from_sheet`` helper below is the reusable core. To add another
prompt-driven job:

1. Add a new ``GoogleSheetsResource(...)`` instance in
   ``dagster_project/resources/google_sheets.py`` with its own env vars, and
   register it in ``RESOURCES``.
2. Write a new asset that injects that sheet resource + ``openai_client`` and
   calls ``run_prompt_from_sheet(...)`` with your sheet's tab/cell names.
3. Wire it up in a ``define_asset_job`` under ``jobs/``.
"""

from datetime import datetime, timezone

from dagster import AssetExecutionContext, asset

from dagster_project.resources import GoogleSheetsResource, OpenAIResource

RESPONSES_HEADER = ["run_at", "prompt", "model", "response"]


def run_prompt_from_sheet(
    *,
    sheet: GoogleSheetsResource,
    openai: OpenAIResource,
    prompt_tab: str,
    prompt_cell: str,
    output_tab: str,
    model_cell: str | None = None,
    system: str | None = None,
) -> dict:
    """Read prompt from ``sheet``, call OpenAI, append result to ``output_tab``.

    Returns a dict with keys ``prompt``, ``model``, ``response``, ``run_at``.
    Raises ``ValueError`` if the prompt cell is blank.
    """
    prompt = sheet.read_cell(prompt_tab, prompt_cell)
    if not prompt:
        raise ValueError(f"No prompt found at {prompt_tab}!{prompt_cell}")

    model_override = sheet.read_cell(prompt_tab, model_cell) if model_cell else ""
    model = model_override or None

    response = openai.complete(prompt, model=model, system=system)
    run_at = datetime.now(timezone.utc).isoformat()
    effective_model = model or openai.default_model

    sheet.append_row_with_header(
        worksheet_name=output_tab,
        row=[run_at, prompt, effective_model, response],
        header=RESPONSES_HEADER,
    )

    return {
        "prompt": prompt,
        "model": effective_model,
        "response": response,
        "run_at": run_at,
    }


@asset(group_name="exports")
def read_prompt_from_sheet(
    context: AssetExecutionContext,
    llm_prompt_google_sheet: GoogleSheetsResource,
) -> dict:
    """Read the user prompt (and optional model override) from the Prompt tab."""
    prompt = llm_prompt_google_sheet.read_cell("Prompt", "B1")
    model = llm_prompt_google_sheet.read_cell("Prompt", "B2") or None

    if not prompt:
        raise ValueError("Prompt!B1 is empty — stakeholder must set a prompt")

    context.add_output_metadata({"prompt_preview": prompt[:200], "model": model or ""})
    return {"prompt": prompt, "model": model}


@asset(group_name="exports")
def run_prompt_and_write_result(
    context: AssetExecutionContext,
    read_prompt_from_sheet: dict,
    llm_prompt_google_sheet: GoogleSheetsResource,
    openai_client: OpenAIResource,
) -> None:
    """Run the prompt against OpenAI and append the response to the Responses tab."""
    del read_prompt_from_sheet  # dependency only; runner re-reads to stay atomic

    result = run_prompt_from_sheet(
        sheet=llm_prompt_google_sheet,
        openai=openai_client,
        prompt_tab="Prompt",
        prompt_cell="B1",
        output_tab="Responses",
        model_cell="B2",
    )

    context.log.info(
        f"Wrote response ({len(result['response'])} chars) using model {result['model']}"
    )
    context.add_output_metadata(
        {
            "response_preview": result["response"][:200],
            "model": result["model"],
            "run_at": result["run_at"],
        }
    )
