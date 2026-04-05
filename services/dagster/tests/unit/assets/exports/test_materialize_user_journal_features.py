"""Unit tests for materialize_user_journal_features asset."""

from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

from dagster import build_op_context
import pytest

from dagster_project.assets.exports.materialize_user_journal_features import (
    materialize_user_journal_features,
)


def _make_store(feature_view_name: str = "user_journal_summary_features") -> MagicMock:
    store = MagicMock()
    store.config.online_store = {"type": "redis"}
    store.config.offline_store = {"type": "postgres"}
    store.get_feature_view.return_value = SimpleNamespace(name=feature_view_name)
    return store


def _make_feast_resource(store: MagicMock, repo_path: Path) -> MagicMock:
    feast_resource = MagicMock()
    feast_resource.repo_path = str(repo_path)
    feast_resource.get_store.return_value.__enter__.return_value = store
    return feast_resource


@pytest.mark.unit
class TestMaterializeUserJournalFeatures:
    """Test Feast feature materialization asset behavior."""

    def test_materializes_existing_feature_view(self, tmp_path):
        context = build_op_context()
        context.log.info = MagicMock()

        store = _make_store()
        feast_resource = _make_feast_resource(store, tmp_path)

        result = materialize_user_journal_features(context, feast_resource)

        store.get_feature_view.assert_called_once_with("user_journal_summary_features")
        store.apply.assert_not_called()
        store.materialize.assert_called_once()
        assert result["status"] == "success"
        assert result["feature_view"] == "user_journal_summary_features"
        assert "materialized_at" in result

    def test_applies_feature_view_when_missing(self, monkeypatch, tmp_path):
        context = build_op_context()
        context.log.info = MagicMock()

        store = _make_store()
        store.get_feature_view.side_effect = [
            Exception("missing"),
            SimpleNamespace(name="user_journal_summary_features"),
        ]
        feast_resource = _make_feast_resource(store, tmp_path)

        entities_module = ModuleType("entities")
        entities_module.user_entity = object()
        feature_views_module = ModuleType("feature_views")
        feature_views_module.user_journal_summary_fv = object()
        monkeypatch.setitem(sys.modules, "entities", entities_module)
        monkeypatch.setitem(sys.modules, "feature_views", feature_views_module)

        repo_path_str = str(tmp_path)
        assert repo_path_str not in sys.path

        result = materialize_user_journal_features(context, feast_resource)

        store.apply.assert_called_once_with(
            [entities_module.user_entity, feature_views_module.user_journal_summary_fv]
        )
        assert store.get_feature_view.call_count == 2
        assert repo_path_str not in sys.path
        assert result["status"] == "success"

    def test_cleans_up_sys_path_when_apply_fails(self, tmp_path):
        context = build_op_context()
        context.log.info = MagicMock()

        store = _make_store()
        store.get_feature_view.side_effect = Exception("missing")
        feast_resource = _make_feast_resource(store, tmp_path)

        repo_path_str = str(tmp_path)
        assert repo_path_str not in sys.path

        with pytest.raises(ValueError, match="Failed to apply feature views"):
            materialize_user_journal_features(context, feast_resource)

        assert repo_path_str not in sys.path
