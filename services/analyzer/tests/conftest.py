import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture()
def client_fixture():
    client = TestClient(app)

    yield client
