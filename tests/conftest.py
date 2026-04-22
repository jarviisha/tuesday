import pytest

from tuesday_rag.runtime.container import container


@pytest.fixture(autouse=True)
def reset_container_state() -> None:
    container.vector_store.reset()
