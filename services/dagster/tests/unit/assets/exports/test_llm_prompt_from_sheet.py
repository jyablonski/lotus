"""Unit tests for the LLM-prompt-from-sheet runner and assets."""

from unittest.mock import MagicMock

from dagster import ResourceDefinition, build_op_context
import pytest

from dagster_project.assets.exports.llm_prompt_from_sheet import (
    RESPONSES_HEADER,
    read_prompt_from_sheet,
    run_prompt_and_write_result,
    run_prompt_from_sheet,
)


def _build_sheet_mock(
    cells: dict[tuple[str, str], str] | None = None,
) -> MagicMock:
    """Build a mock GoogleSheetsResource with configurable ``read_cell`` outputs."""
    cells = cells or {}
    mock = MagicMock()

    def _read_cell(tab: str, cell: str) -> str:
        return cells.get((tab, cell), "")

    mock.read_cell.side_effect = _read_cell
    return mock


def _build_openai_mock(
    response: str = "hello back", default_model: str = "gpt-4o-mini"
) -> MagicMock:
    mock = MagicMock()
    mock.default_model = default_model
    mock.complete.return_value = response
    return mock


@pytest.mark.unit
class TestRunPromptFromSheet:
    def test_happy_path_appends_row_with_header(self):
        sheet = _build_sheet_mock({("Prompt", "B1"): "say hi", ("Prompt", "B2"): ""})
        openai = _build_openai_mock("hi!")

        result = run_prompt_from_sheet(
            sheet=sheet,
            openai=openai,
            prompt_tab="Prompt",
            prompt_cell="B1",
            output_tab="Responses",
            model_cell="B2",
        )

        assert result["prompt"] == "say hi"
        assert result["response"] == "hi!"
        assert result["model"] == "gpt-4o-mini"
        assert result["run_at"]

        openai.complete.assert_called_once_with("say hi", model=None, system=None)
        sheet.append_row_with_header.assert_called_once()
        kwargs = sheet.append_row_with_header.call_args.kwargs
        assert kwargs["worksheet_name"] == "Responses"
        assert kwargs["header"] == RESPONSES_HEADER
        row = kwargs["row"]
        assert row[1] == "say hi"
        assert row[2] == "gpt-4o-mini"
        assert row[3] == "hi!"

    def test_model_override_from_cell(self):
        sheet = _build_sheet_mock(
            {("Prompt", "B1"): "say hi", ("Prompt", "B2"): "gpt-4o"}
        )
        openai = _build_openai_mock("hi!")

        result = run_prompt_from_sheet(
            sheet=sheet,
            openai=openai,
            prompt_tab="Prompt",
            prompt_cell="B1",
            output_tab="Responses",
            model_cell="B2",
        )

        assert result["model"] == "gpt-4o"
        openai.complete.assert_called_once_with("say hi", model="gpt-4o", system=None)

    def test_raises_when_prompt_blank(self):
        sheet = _build_sheet_mock({("Prompt", "B1"): ""})
        openai = _build_openai_mock()

        with pytest.raises(ValueError, match="No prompt found at Prompt!B1"):
            run_prompt_from_sheet(
                sheet=sheet,
                openai=openai,
                prompt_tab="Prompt",
                prompt_cell="B1",
                output_tab="Responses",
            )

        openai.complete.assert_not_called()
        sheet.append_row_with_header.assert_not_called()

    def test_no_model_cell_skips_read(self):
        sheet = _build_sheet_mock({("Prompt", "B1"): "hi"})
        openai = _build_openai_mock("ok")

        run_prompt_from_sheet(
            sheet=sheet,
            openai=openai,
            prompt_tab="Prompt",
            prompt_cell="B1",
            output_tab="Responses",
            model_cell=None,
        )

        # read_cell called only once (for the prompt), not for a model cell
        assert sheet.read_cell.call_count == 1


def _context_with_sheet(
    sheet_resource: MagicMock, openai_resource: MagicMock | None = None
):
    resources = {
        "llm_prompt_google_sheet": ResourceDefinition(
            resource_fn=lambda _c: sheet_resource
        )
    }
    if openai_resource is not None:
        resources["openai_client"] = ResourceDefinition(
            resource_fn=lambda _c: openai_resource
        )
    context = build_op_context(resources=resources)
    context.log.info = MagicMock()
    return context


@pytest.mark.unit
class TestReadPromptAsset:
    def test_returns_prompt_and_model(self):
        sheet = _build_sheet_mock(
            {("Prompt", "B1"): "summarize", ("Prompt", "B2"): "gpt-4o"}
        )
        context = _context_with_sheet(sheet)

        result = read_prompt_from_sheet(context, sheet)

        assert result == {"prompt": "summarize", "model": "gpt-4o"}

    def test_model_none_when_b2_blank(self):
        sheet = _build_sheet_mock({("Prompt", "B1"): "summarize"})
        context = _context_with_sheet(sheet)

        result = read_prompt_from_sheet(context, sheet)

        assert result == {"prompt": "summarize", "model": None}

    def test_raises_when_prompt_blank(self):
        sheet = _build_sheet_mock({("Prompt", "B1"): ""})
        context = _context_with_sheet(sheet)

        with pytest.raises(ValueError, match="Prompt!B1 is empty"):
            read_prompt_from_sheet(context, sheet)


@pytest.mark.unit
class TestRunPromptAndWriteResultAsset:
    def test_delegates_to_runner(self):
        sheet = _build_sheet_mock({("Prompt", "B1"): "say hi", ("Prompt", "B2"): ""})
        openai = _build_openai_mock("hello!")
        context = _context_with_sheet(sheet, openai)

        result = run_prompt_and_write_result(
            context,
            {"prompt": "say hi", "model": None},
            sheet,
            openai,
        )

        assert result is None
        openai.complete.assert_called_once_with("say hi", model=None, system=None)
        sheet.append_row_with_header.assert_called_once()
