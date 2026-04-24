from typing import Any

from tuesday.rag.domain.models import RetrievalRequest, RetrievedChunk
from tuesday.rag.retrieval.service import RetrieverService


class StubEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class StubVectorStore:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = chunks

    def replace_document(
        self,
        *,
        index_name: str,
        document_id: str,
        chunks: list[Any],
    ) -> bool:
        return False

    def query(
        self,
        *,
        index_name: str,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None,
    ) -> list[RetrievedChunk]:
        return list(self._chunks)


def test_regression_retrieval_prefers_lexically_supported_chunks() -> None:
    retriever = RetrieverService(
        StubEmbeddingProvider(),
        StubVectorStore(
            [
                RetrievedChunk(
                    chunk_id="chunk-broad-policy",
                    document_id="doc-policy",
                    text="Chinh sach hoan tien duoc tiep nhan qua cong ho tro chinh thuc.",
                    score=0.95,
                    metadata={},
                ),
                RetrievedChunk(
                    chunk_id="chunk-timeline",
                    document_id="doc-refund",
                    text=(
                        "Khach hang co the yeu cau hoan tien trong vong 7 ngay "
                        "ke tu ngay thanh toan."
                    ),
                    score=0.73,
                    metadata={},
                ),
                RetrievedChunk(
                    chunk_id="chunk-unrelated",
                    document_id="doc-hr",
                    text="Nhan su moi phai nop bang cap va giay to onboarding.",
                    score=0.99,
                    metadata={},
                ),
            ]
        ),
    )

    result = retriever.retrieve(
        RetrievalRequest(
            query="Khach hang duoc hoan tien trong bao lau?",
            top_k=3,
            filters=None,
            index_name="enterprise-kb",
        )
    )

    assert [chunk.chunk_id for chunk in result.chunks] == [
        "chunk-timeline",
        "chunk-broad-policy",
    ]


def test_regression_retrieval_respects_top_k_after_lexical_rerank() -> None:
    retriever = RetrieverService(
        StubEmbeddingProvider(),
        StubVectorStore(
            [
                RetrievedChunk(
                    chunk_id="chunk-broad-policy",
                    document_id="doc-policy",
                    text="Chinh sach hoan tien duoc tiep nhan qua cong ho tro chinh thuc.",
                    score=0.95,
                    metadata={},
                ),
                RetrievedChunk(
                    chunk_id="chunk-timeline",
                    document_id="doc-refund",
                    text=(
                        "Khach hang co the yeu cau hoan tien trong vong 7 ngay "
                        "ke tu ngay thanh toan."
                    ),
                    score=0.73,
                    metadata={},
                ),
            ]
        ),
    )

    result = retriever.retrieve(
        RetrievalRequest(
            query="Khach hang duoc hoan tien trong bao lau?",
            top_k=1,
            filters=None,
            index_name="enterprise-kb",
        )
    )

    assert [chunk.chunk_id for chunk in result.chunks] == ["chunk-timeline"]
