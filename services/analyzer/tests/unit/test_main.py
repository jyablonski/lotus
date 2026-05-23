from unittest.mock import AsyncMock, Mock

from fastapi import HTTPException
from fastapi.responses import JSONResponse
import pytest
from src import main as main_module


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_auth_middleware_allows_unprotected_path():
    request = Mock()
    request.method = "GET"
    request.url.path = "/health"
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))

    response = await main_module.auth_middleware(request, call_next)

    assert response.status_code == 200
    call_next.assert_awaited_once_with(request)


@pytest.mark.anyio
async def test_auth_middleware_rejects_invalid_token():
    request = Mock()
    request.method = "GET"
    request.url.path = "/v1/secure"
    request.headers.get.return_value = "Bearer wrong"

    response = await main_module.auth_middleware(request, AsyncMock())

    assert response.status_code == 401
    assert response.body == b'{"detail":"unauthorized"}'


@pytest.mark.anyio
async def test_auth_middleware_allows_valid_token():
    request = Mock()
    request.method = "GET"
    request.url.path = "/v1/secure"
    request.headers.get.return_value = f"Bearer {main_module._ANALYZER_API_KEY}"
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))

    response = await main_module.auth_middleware(request, call_next)

    assert response.status_code == 200
    call_next.assert_awaited_once_with(request)


@pytest.mark.anyio
async def test_root_and_health_endpoints(monkeypatch):
    assert await main_module.root() == {"message": "Hello World"}

    request = Mock()
    request.app.state.model_load_status = {
        "status": "loaded",
        "models": [{"name": "topic", "ready": True}],
    }
    wait_for_ready = AsyncMock(return_value=None)
    monkeypatch.setattr(main_module, "_wait_for_models_ready", wait_for_ready)

    assert await main_module.health(request) == {
        "status": "healthy",
        "service": "analyzer",
        "models": [{"name": "topic", "ready": True}],
    }
    wait_for_ready.assert_awaited_once_with(request.app)


@pytest.mark.anyio
async def test_health_waits_for_models_to_be_ready(monkeypatch):
    request = Mock()
    request.app.state.model_load_status = {"status": "loading", "models": []}
    wait_for_ready = AsyncMock(side_effect=TimeoutError)
    monkeypatch.setattr(main_module, "_wait_for_models_ready", wait_for_ready)

    with pytest.raises(HTTPException) as exc_info:
        await main_module.health(request)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["models"]["status"] == "loading"
    wait_for_ready.assert_awaited_once_with(request.app)


@pytest.mark.anyio
async def test_custom_404_handler_uses_exception_detail():
    exc = HTTPException(status_code=404, detail="missing")

    response = await main_module.custom_404_handler(Mock(), exc)

    assert response.status_code == 404
    assert response.body == b'{"detail":"missing"}'


@pytest.mark.anyio
async def test_custom_404_handler_uses_default_detail():
    response = await main_module.custom_404_handler(Mock(), Exception("no detail"))

    assert response.status_code == 404
    assert b"this doesn't exist hoe" in response.body


@pytest.mark.anyio
async def test_lifespan_loads_models(monkeypatch):
    topic_client = Mock()
    sentiment_client = Mock()
    embedding_client = Mock()
    topic_client.is_ready.return_value = True
    sentiment_client.is_ready.return_value = True
    embedding_client.is_ready.return_value = True
    topic_client.get_model_info.return_value = {"status": "loaded"}
    sentiment_client.get_model_info.return_value = {"status": "loaded"}
    embedding_client.get_model_info.return_value = {"status": "loaded"}
    monkeypatch.setattr(main_module, "get_topic_client", Mock(return_value=topic_client))
    monkeypatch.setattr(main_module, "get_sentiment_client", Mock(return_value=sentiment_client))
    monkeypatch.setattr(main_module, "get_embedding_client", Mock(return_value=embedding_client))

    async def load_model(_name, load):
        load()

    monkeypatch.setattr(main_module, "_load_startup_model", load_model)

    async with main_module.lifespan(main_module.app):
        pass

    topic_client.load_model.assert_called_once()
    sentiment_client.load_model.assert_called_once()
    main_module.get_embedding_client.assert_called()
    assert main_module.app.state.models_ready.is_set()


@pytest.mark.anyio
async def test_lifespan_reraises_load_failures(monkeypatch):
    topic_client = Mock()
    topic_client.load_model.side_effect = RuntimeError("boom")
    sentiment_client = Mock()
    embedding_client = Mock()
    monkeypatch.setattr(main_module, "get_topic_client", Mock(return_value=topic_client))
    monkeypatch.setattr(main_module, "get_sentiment_client", Mock(return_value=sentiment_client))
    monkeypatch.setattr(main_module, "get_embedding_client", Mock(return_value=embedding_client))

    async def load_model(_name, load):
        load()

    monkeypatch.setattr(main_module, "_load_startup_model", load_model)

    with pytest.raises(RuntimeError, match="boom"):
        async with main_module.lifespan(main_module.app):
            pass
