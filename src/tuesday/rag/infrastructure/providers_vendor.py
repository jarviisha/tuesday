import json

from tuesday.rag.domain.models import LLMGenerationResult
from tuesday.rag.infrastructure.http_client import post_json

JSON_GENERATION_INSTRUCTION = (
    "Return only valid JSON with schema "
    '{"answer":"string","citations":["chunk-id"]}. '
    "Do not wrap the JSON in markdown fences. "
    "Citations must contain only chunk_id values that appear in the provided context."
)


class OpenAIEmbeddingProvider:
    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = post_json(
            url=f"{self._base_url}/embeddings",
            headers={"Authorization": f"Bearer {self._api_key}"},
            payload={
                "model": self._model,
                "input": texts,
                "encoding_format": "float",
            },
        )
        return [item["embedding"] for item in response["data"]]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class OpenAILLMProvider:
    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def generate_text(self, prompt: str) -> LLMGenerationResult:
        response = post_json(
            url=f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            payload={
                "model": self._model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "developer", "content": JSON_GENERATION_INSTRUCTION},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        content = response["choices"][0]["message"]["content"]
        return _parse_generation_result(content)


class GeminiEmbeddingProvider:
    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = _gemini_model_path(model)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text, task_type="RETRIEVAL_DOCUMENT") for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text, task_type="RETRIEVAL_QUERY")

    def _embed(self, text: str, *, task_type: str) -> list[float]:
        response = post_json(
            url=f"{self._base_url}/{self._model}:embedContent?key={self._api_key}",
            headers={},
            payload={
                "content": {"parts": [{"text": text}]},
                "taskType": task_type,
            },
        )
        return response["embedding"]["values"]


class GeminiLLMProvider:
    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = _gemini_model_path(model)

    def generate_text(self, prompt: str) -> LLMGenerationResult:
        response = post_json(
            url=f"{self._base_url}/{self._model}:generateContent?key={self._api_key}",
            headers={},
            payload={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": (
                                    f"{JSON_GENERATION_INSTRUCTION}\n\n"
                                    f"{prompt}"
                                )
                            }
                        ]
                    }
                ]
            },
        )
        content = response["candidates"][0]["content"]["parts"][0]["text"]
        return _parse_generation_result(content)


class AzureOpenAIEmbeddingProvider:
    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str,
        api_version: str,
        deployment: str,
    ) -> None:
        self._api_key = api_key
        self._endpoint = endpoint.rstrip("/")
        self._api_version = api_version
        self._deployment = deployment

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = post_json(
            url=(
                f"{self._endpoint}/openai/deployments/{self._deployment}/embeddings"
                f"?api-version={self._api_version}"
            ),
            headers={"api-key": self._api_key},
            payload={"input": texts},
        )
        return [item["embedding"] for item in response["data"]]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class AzureOpenAILLMProvider:
    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str,
        api_version: str,
        deployment: str,
    ) -> None:
        self._api_key = api_key
        self._endpoint = endpoint.rstrip("/")
        self._api_version = api_version
        self._deployment = deployment

    def generate_text(self, prompt: str) -> LLMGenerationResult:
        response = post_json(
            url=(
                f"{self._endpoint}/openai/deployments/{self._deployment}/chat/completions"
                f"?api-version={self._api_version}"
            ),
            headers={"api-key": self._api_key},
            payload={
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": JSON_GENERATION_INSTRUCTION},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        content = response["choices"][0]["message"]["content"]
        return _parse_generation_result(content)


def _gemini_model_path(model: str) -> str:
    if model.startswith("models/"):
        return model
    return f"models/{model}"


def _parse_generation_result(raw_content: str) -> LLMGenerationResult:
    payload = _extract_json_object(raw_content)
    answer = payload.get("answer")
    citations = payload.get("citations", [])
    if not isinstance(answer, str):
        raise RuntimeError("provider generation output is invalid")
    if not isinstance(citations, list) or not all(isinstance(item, str) for item in citations):
        raise RuntimeError("provider generation output is invalid")
    return LLMGenerationResult(answer=answer.strip(), citations=citations)


def _extract_json_object(raw_content: str) -> dict:
    stripped = raw_content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end < start:
            raise RuntimeError("provider generation output is invalid") from None
        payload = json.loads(stripped[start : end + 1])
    if not isinstance(payload, dict):
        raise RuntimeError("provider generation output is invalid")
    return payload
