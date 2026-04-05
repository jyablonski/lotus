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
async def test_root_and_health_endpoints():
    assert await main_module.root() == {"message": "Hello World"}
    assert await main_module.health() == {"status": "healthy"}


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
    monkeypatch.setattr(main_module, "get_topic_client", Mock(return_value=topic_client))
    monkeypatch.setattr(main_module, "get_sentiment_client", Mock(return_value=sentiment_client))

    async with main_module.lifespan(main_module.app):
        pass

    topic_client.load_model.assert_called_once()
    sentiment_client.load_model.assert_called_once()


@pytest.mark.anyio
async def test_lifespan_reraises_load_failures(monkeypatch):
    topic_client = Mock()
    topic_client.load_model.side_effect = RuntimeError("boom")
    monkeypatch.setattr(main_module, "get_topic_client", Mock(return_value=topic_client))

    with pytest.raises(RuntimeError, match="boom"):
        async with main_module.lifespan(main_module.app):
            pass
