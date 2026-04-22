from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError


class RetryableDependencyError(Exception):
    pass


class IntegrationTimeoutError(Exception):
    def __init__(self, component: str, timeout_ms: int) -> None:
        super().__init__(f"{component} timed out after {timeout_ms}ms")
        self.component = component
        self.timeout_ms = timeout_ms


class RetryExhaustedError(Exception):
    def __init__(self, component: str, attempts: int) -> None:
        super().__init__(f"{component} exhausted retries after {attempts} attempts")
        self.component = component
        self.attempts = attempts


def _is_retryable(exc: Exception) -> bool:
    return isinstance(exc, (ConnectionError, OSError, RetryableDependencyError))


def run_with_resilience[T](
    operation: Callable[[], T],
    *,
    component: str,
    timeout_ms: int,
    max_retries: int,
) -> T:
    attempts = 0
    last_error: Exception | None = None
    max_attempts = max_retries + 1
    with ThreadPoolExecutor(max_workers=1) as executor:
        while attempts < max_attempts:
            attempts += 1
            future = executor.submit(operation)
            try:
                return future.result(timeout=timeout_ms / 1000)
            except FutureTimeoutError:
                future.cancel()
                last_error = IntegrationTimeoutError(component, timeout_ms)
                if attempts >= max_attempts:
                    raise RetryExhaustedError(component, attempts) from last_error
            except Exception as exc:
                last_error = exc
                if not _is_retryable(exc):
                    raise
                if attempts >= max_attempts:
                    raise RetryExhaustedError(component, attempts) from exc
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"{component} failed without an explicit error")


class ResilientEmbeddingProvider:
    def __init__(self, provider, *, timeout_ms: int, max_retries: int) -> None:
        self._provider = provider
        self._timeout_ms = timeout_ms
        self._max_retries = max_retries

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return run_with_resilience(
            lambda: self._provider.embed_texts(texts),
            component="embedding_provider",
            timeout_ms=self._timeout_ms,
            max_retries=self._max_retries,
        )

    def embed_query(self, text: str) -> list[float]:
        return run_with_resilience(
            lambda: self._provider.embed_query(text),
            component="embedding_provider",
            timeout_ms=self._timeout_ms,
            max_retries=self._max_retries,
        )


class ResilientLLMProvider:
    def __init__(self, provider, *, timeout_ms: int, max_retries: int) -> None:
        self._provider = provider
        self._timeout_ms = timeout_ms
        self._max_retries = max_retries

    def generate_text(self, prompt: str):
        return run_with_resilience(
            lambda: self._provider.generate_text(prompt),
            component="generation_provider",
            timeout_ms=self._timeout_ms,
            max_retries=self._max_retries,
        )


class ResilientVectorStore:
    def __init__(self, store, *, timeout_ms: int, max_retries: int) -> None:
        self._store = store
        self._timeout_ms = timeout_ms
        self._max_retries = max_retries

    def replace_document(
        self,
        *,
        index_name: str,
        document_id: str,
        chunks: list,
    ) -> bool:
        return run_with_resilience(
            lambda: self._store.replace_document(
                index_name=index_name,
                document_id=document_id,
                chunks=chunks,
            ),
            component="vector_store",
            timeout_ms=self._timeout_ms,
            max_retries=self._max_retries,
        )

    def query(
        self,
        *,
        index_name: str,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None,
    ):
        return run_with_resilience(
            lambda: self._store.query(
                index_name=index_name,
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters,
            ),
            component="vector_store",
            timeout_ms=self._timeout_ms,
            max_retries=self._max_retries,
        )

    def reset(self) -> None:
        if hasattr(self._store, "reset"):
            self._store.reset()
