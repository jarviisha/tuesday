import httpx
import pytest

from tuesday.api.app import create_app
from tuesday.runtime.config import RuntimeConfig
from tuesday.runtime.container import build_container


@pytest.fixture
def runtime_container():
    container = build_container(RuntimeConfig())
    container.vector_store.reset()
    return container


@pytest.fixture
async def api_app(monkeypatch: pytest.MonkeyPatch):
    def build_test_runtime():
        return build_container(RuntimeConfig())

    monkeypatch.setattr("tuesday.api.app.build_runtime_from_env", build_test_runtime)
    app = create_app()
    async with app.router.lifespan_context(app):
        yield app


@pytest.fixture
async def api_client(api_app):
    transport = httpx.ASGITransport(app=api_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
