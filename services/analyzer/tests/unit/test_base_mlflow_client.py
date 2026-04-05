from unittest.mock import Mock

import pytest
from src.clients import base_mlflow_client as base_module
from src.clients.base_mlflow_client import BaseMLflowClient


class DummyMLflowClient(BaseMLflowClient):
    def __init__(self):
        super().__init__(model_name="dummy_model", mlflow_uri="http://mlflow.test")


def test_load_model_returns_early_when_already_loaded(monkeypatch):
    client = DummyMLflowClient()
    client._is_loaded = True
    load_model = Mock()
    monkeypatch.setattr(base_module, "_pyfunc_load_model", load_model)

    client.load_model()

    load_model.assert_not_called()


def test_load_model_sets_latest_version_and_run_id(monkeypatch):
    client = DummyMLflowClient()
    fake_model = object()
    version_1 = Mock(version="1")
    version_3 = Mock(version="3")
    mlflow_client = Mock()
    mlflow_client.search_model_versions.return_value = [version_1, version_3]
    mlflow_client.get_model_version.return_value = Mock(run_id="run-123")

    monkeypatch.setattr(base_module, "_pyfunc_load_model", Mock(return_value=fake_model))
    monkeypatch.setattr(base_module.mlflow, "set_tracking_uri", Mock())
    monkeypatch.setattr(base_module.mlflow, "MlflowClient", Mock(return_value=mlflow_client))

    client.load_model()

    assert client.model is fake_model
    assert client.model_version == "3"
    assert client.model_run_id == "run-123"
    assert client._is_loaded is True


def test_load_model_uses_explicit_version(monkeypatch):
    client = DummyMLflowClient()
    mlflow_client = Mock()
    mlflow_client.get_model_version.return_value = Mock(run_id="run-explicit")

    monkeypatch.setattr(base_module, "_pyfunc_load_model", Mock(return_value=object()))
    monkeypatch.setattr(base_module.mlflow, "set_tracking_uri", Mock())
    monkeypatch.setattr(base_module.mlflow, "MlflowClient", Mock(return_value=mlflow_client))

    client.load_model("7")

    assert client.model_version == "7"
    assert client.model_run_id == "run-explicit"
    mlflow_client.search_model_versions.assert_not_called()


def test_load_model_falls_back_to_latest_when_version_lookup_fails(monkeypatch):
    client = DummyMLflowClient()
    mlflow_client = Mock()
    mlflow_client.search_model_versions.side_effect = RuntimeError("api down")
    mlflow_client.get_model_version.return_value = Mock(run_id="run-fallback")

    monkeypatch.setattr(base_module, "_pyfunc_load_model", Mock(return_value=object()))
    monkeypatch.setattr(base_module.mlflow, "set_tracking_uri", Mock())
    monkeypatch.setattr(base_module.mlflow, "MlflowClient", Mock(return_value=mlflow_client))

    client.load_model()

    assert client.model_version == "latest"
    assert client.model_run_id == "run-fallback"


def test_load_model_sets_unknown_run_id_when_metadata_lookup_fails(monkeypatch):
    client = DummyMLflowClient()
    mlflow_client = Mock()
    mlflow_client.search_model_versions.return_value = [Mock(version="2")]
    mlflow_client.get_model_version.side_effect = RuntimeError("metadata missing")

    monkeypatch.setattr(base_module, "_pyfunc_load_model", Mock(return_value=object()))
    monkeypatch.setattr(base_module.mlflow, "set_tracking_uri", Mock())
    monkeypatch.setattr(base_module.mlflow, "MlflowClient", Mock(return_value=mlflow_client))

    client.load_model()

    assert client.model_version == "2"
    assert client.model_run_id == "unknown"


def test_load_model_raises_when_pyfunc_returns_none(monkeypatch):
    client = DummyMLflowClient()
    monkeypatch.setattr(base_module, "_pyfunc_load_model", Mock(return_value=None))
    monkeypatch.setattr(base_module.mlflow, "set_tracking_uri", Mock())

    with pytest.raises(RuntimeError, match="returned None"):
        client.load_model()


def test_get_model_info_returns_not_loaded_when_unready():
    client = DummyMLflowClient()

    assert client.get_model_info() == {"status": "not_loaded"}


def test_get_model_info_returns_metadata_when_ready():
    client = DummyMLflowClient()
    client.model = object()
    client._is_loaded = True
    client.model_version = "5"
    client.model_run_id = "run-5"

    assert client.get_model_info() == {
        "model_name": "dummy_model",
        "model_version": "5",
        "run_id": "run-5",
        "mlflow_uri": "http://mlflow.test",
        "status": "loaded",
    }


def test_is_ready_returns_false_when_missing_model():
    client = DummyMLflowClient()
    client._is_loaded = True
    client.model = None

    assert client.is_ready() is False
