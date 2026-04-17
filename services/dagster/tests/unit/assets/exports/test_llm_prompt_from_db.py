"""Unit tests for the LLM-prompt-from-db runner and assets."""

from contextlib import contextmanager
from unittest.mock import MagicMock

from dagster import ResourceDefinition, build_op_context
import pytest

from dagster_project.assets.exports.llm_prompt_from_db import (
    SALES_OUTREACH_APPLICATION,
    fetch_stakeholder_prompt,
    read_sales_outreach_prompt,
    run_db_prompt_and_write_result,
    run_prompt_from_db,
    write_stakeholder_prompt_response,
)


def _build_postgres_mock(row: tuple | None = None) -> MagicMock:
    """Build a mock PostgresResource whose get_connection() yields a cursor
    configured to return ``row`` from fetchone()."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = row

    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = False

    mock_resource = MagicMock()

    @contextmanager
    def _get_connection():
        yield mock_conn

    mock_resource.get_connection.side_effect = _get_connection
    mock_resource._cursor = mock_cursor
    mock_resource._conn = mock_conn
    return mock_resource


def _build_openai_mock(
    response: str = "hello back", default_model: str = "gpt-4o-mini"
) -> MagicMock:
    mock = MagicMock()
    mock.default_model = default_model
    mock.complete.return_value = response
    return mock


@pytest.mark.unit
class TestFetchStakeholderPrompt:
    def test_returns_row_as_dict(self):
        postgres = _build_postgres_mock(
            row=("abc-123", "sales", "sales_outreach", "say hi")
        )

        result = fetch_stakeholder_prompt(postgres, "sales_outreach")

        assert result == {
            "id": "abc-123",
            "stakeholder_group": "sales",
            "application": "sales_outreach",
            "prompt": "say hi",
        }
        postgres._cursor.execute.assert_called_once()
        args = postgres._cursor.execute.call_args.args
        assert args[1] == ("sales_outreach",)

    def test_raises_when_row_not_found(self):
        postgres = _build_postgres_mock(row=None)

        with pytest.raises(ValueError, match="No stakeholder_prompts row"):
            fetch_stakeholder_prompt(postgres, "unknown_app")


@pytest.mark.unit
class TestWriteStakeholderPromptResponse:
    def test_insert_and_commit(self):
        postgres = _build_postgres_mock()

        write_stakeholder_prompt_response(
            postgres=postgres,
            stakeholder_prompt_id="abc-123",
            model="gpt-4o-mini",
            response="hi!",
        )

        postgres._cursor.execute.assert_called_once()
        args = postgres._cursor.execute.call_args.args
        assert args[1] == ("abc-123", "gpt-4o-mini", "hi!")
        postgres._conn.commit.assert_called_once()


@pytest.mark.unit
class TestRunPromptFromDb:
    def test_happy_path(self, monkeypatch):
        postgres = _build_postgres_mock(
            row=("abc-123", "sales", "sales_outreach", "say hi")
        )
        openai = _build_openai_mock("hi!")

        result = run_prompt_from_db(
            postgres=postgres,
            openai=openai,
            application="sales_outreach",
        )

        assert result == {
            "stakeholder_prompt_id": "abc-123",
            "application": "sales_outreach",
            "prompt": "say hi",
            "model": "gpt-4o-mini",
            "response": "hi!",
        }
        openai.complete.assert_called_once_with("say hi", model=None, system=None)
        # Both execute calls (select then insert) happened
        assert postgres._cursor.execute.call_count == 2

    def test_model_override_is_persisted(self):
        postgres = _build_postgres_mock(
            row=("abc-123", "sales", "sales_outreach", "say hi")
        )
        openai = _build_openai_mock("hi!")

        result = run_prompt_from_db(
            postgres=postgres,
            openai=openai,
            application="sales_outreach",
            model="gpt-4o",
        )

        assert result["model"] == "gpt-4o"
        openai.complete.assert_called_once_with("say hi", model="gpt-4o", system=None)
        insert_args = postgres._cursor.execute.call_args_list[1].args
        assert insert_args[1] == ("abc-123", "gpt-4o", "hi!")

    def test_raises_when_prompt_blank(self):
        postgres = _build_postgres_mock(row=("abc-123", "sales", "sales_outreach", ""))
        openai = _build_openai_mock()

        with pytest.raises(ValueError, match="has an empty prompt"):
            run_prompt_from_db(
                postgres=postgres,
                openai=openai,
                application="sales_outreach",
            )

        openai.complete.assert_not_called()

    def test_raises_when_row_missing(self):
        postgres = _build_postgres_mock(row=None)
        openai = _build_openai_mock()

        with pytest.raises(ValueError, match="No stakeholder_prompts row"):
            run_prompt_from_db(
                postgres=postgres,
                openai=openai,
                application="sales_outreach",
            )


def _context_with_resources(postgres: MagicMock, openai: MagicMock | None = None):
    resources = {
        "postgres_conn": ResourceDefinition(resource_fn=lambda _c: postgres),
    }
    if openai is not None:
        resources["openai_client"] = ResourceDefinition(resource_fn=lambda _c: openai)
    context = build_op_context(resources=resources)
    context.log.info = MagicMock()
    return context


@pytest.mark.unit
class TestReadSalesOutreachPromptAsset:
    def test_returns_prompt_row(self):
        postgres = _build_postgres_mock(
            row=("abc-123", "sales", "sales_outreach", "say hi")
        )
        context = _context_with_resources(postgres)

        result = read_sales_outreach_prompt(context, postgres)

        assert result["application"] == SALES_OUTREACH_APPLICATION
        assert result["prompt"] == "say hi"


@pytest.mark.unit
class TestRunDbPromptAndWriteResultAsset:
    def test_delegates_to_runner(self):
        postgres = _build_postgres_mock(
            row=("abc-123", "sales", "sales_outreach", "say hi")
        )
        openai = _build_openai_mock("hello!")
        context = _context_with_resources(postgres, openai)

        result = run_db_prompt_and_write_result(
            context,
            {
                "id": "abc-123",
                "stakeholder_group": "sales",
                "application": "sales_outreach",
                "prompt": "say hi",
            },
            postgres,
            openai,
        )

        assert result is None
        openai.complete.assert_called_once_with("say hi", model=None, system=None)
        # SELECT + INSERT
        assert postgres._cursor.execute.call_count == 2
