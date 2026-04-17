"""Tests for OpenAIResource."""

from unittest.mock import MagicMock

import pytest

from dagster_project.resources.openai_client import OpenAIResource


def _mock_openai_with_response(text: str) -> MagicMock:
    """Build a mock OpenAI client whose chat.completions.create returns *text*."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = text
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
    return mock_client


@pytest.mark.unit
class TestOpenAIResource:
    def test_defaults(self):
        resource = OpenAIResource(api_key="sk-test")
        assert resource.default_model == "gpt-4o-mini"

    def test_complete_uses_default_model_when_none(self):
        mock_client = _mock_openai_with_response("hi!")
        resource = OpenAIResource(api_key="sk-test")
        resource.get_client = MagicMock(return_value=mock_client)  # type: ignore[method-assign]

        result = resource.complete("hello")

        assert result == "hi!"
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["messages"] == [{"role": "user", "content": "hello"}]

    def test_complete_overrides_model(self):
        mock_client = _mock_openai_with_response("ok")
        resource = OpenAIResource(api_key="sk-test")
        resource.get_client = MagicMock(return_value=mock_client)  # type: ignore[method-assign]

        resource.complete("hello", model="gpt-4o")

        assert mock_client.chat.completions.create.call_args.kwargs["model"] == "gpt-4o"

    def test_complete_includes_system_message(self):
        mock_client = _mock_openai_with_response("ok")
        resource = OpenAIResource(api_key="sk-test")
        resource.get_client = MagicMock(return_value=mock_client)  # type: ignore[method-assign]

        resource.complete("hello", system="be terse")

        messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        assert messages == [
            {"role": "system", "content": "be terse"},
            {"role": "user", "content": "hello"},
        ]

    def test_complete_returns_empty_when_content_is_none(self):
        mock_client = _mock_openai_with_response(None)
        resource = OpenAIResource(api_key="sk-test")
        resource.get_client = MagicMock(return_value=mock_client)  # type: ignore[method-assign]

        assert resource.complete("hello") == ""
