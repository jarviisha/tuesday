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


def test_retriever_drops_zero_overlap_chunks_when_relevant_chunks_exist() -> None:
    retriever = RetrieverService(
        StubEmbeddingProvider(),
        StubVectorStore(
                [
                    RetrievedChunk(
                        chunk_id="chunk-unrelated",
                        document_id="doc-unrelated",
                        text="Quy trinh phe duyet nghi phep cho nhan su noi bo.",
                        score=0.99,
                        metadata={},
                    ),
                RetrievedChunk(
                    chunk_id="chunk-refund",
                    document_id="doc-refund",
                    text="Khach hang co the yeu cau hoan tien trong vong 7 ngay.",
                    score=0.61,
                    metadata={},
                ),
            ]
        ),
    )

    result = retriever.retrieve(
        RetrievalRequest(
            query="Khach hang duoc hoan tien trong bao lau?",
            top_k=2,
            filters=None,
            index_name="enterprise-kb",
        )
    )

    assert [chunk.chunk_id for chunk in result.chunks] == ["chunk-refund"]


def test_retriever_reranks_by_query_token_coverage_before_raw_score() -> None:
    retriever = RetrieverService(
        StubEmbeddingProvider(),
        StubVectorStore(
            [
                RetrievedChunk(
                    chunk_id="chunk-partial",
                    document_id="doc-partial",
                    text="Chinh sach hoan tien duoc xu ly qua cong ho tro.",
                    score=0.92,
                    metadata={},
                ),
                RetrievedChunk(
                    chunk_id="chunk-better-match",
                    document_id="doc-refund",
                    text="Khach hang co the yeu cau hoan tien trong vong 7 ngay.",
                    score=0.74,
                    metadata={},
                ),
            ]
        ),
    )

    result = retriever.retrieve(
        RetrievalRequest(
            query="Khach hang duoc hoan tien trong bao lau?",
            top_k=2,
            filters={"tags": ["refund"]},
            index_name="enterprise-kb",
        )
    )

    assert [chunk.chunk_id for chunk in result.chunks] == [
        "chunk-better-match",
        "chunk-partial",
    ]
