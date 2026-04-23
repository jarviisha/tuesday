import shutil
import subprocess
from pathlib import Path

import pytest

from tuesday.rag.generation.service import GeneratorService
from tuesday.rag.generation.use_case import GenerationUseCase
from tuesday.rag.infrastructure.chunking import CharacterChunker
from tuesday.rag.infrastructure.file_document_parser import LocalFileDocumentParser
from tuesday.rag.infrastructure.providers import DeterministicLLMProvider, HashEmbeddingProvider
from tuesday.rag.infrastructure.vector_store import InMemoryVectorStore
from tuesday.rag.ingestion.file_use_case import FileIngestionUseCase
from tuesday.rag.ingestion.service import IndexerService
from tuesday.rag.ingestion.use_case import IngestionUseCase
from tuesday.rag.retrieval.service import RetrieverService
from tuesday.rag.retrieval.use_case import RetrievalUseCase
from tuesday.runtime.config import RuntimeConfig


def test_file_ingestion_supports_retrieve_and_generate_flow(tmp_path: Path) -> None:
    file_path = tmp_path / "refund-policy.md"
    file_path.write_text(
        (
            "Customers can request a refund within 7 days from the payment date.\n\n"
            "## Refund policy\n\n"
            "Requests must be submitted through the official support portal."
        ),
        encoding="utf-8",
    )

    config = RuntimeConfig()
    vector_store = InMemoryVectorStore()
    embedding_provider = HashEmbeddingProvider()
    ingestion_use_case = IngestionUseCase(
        config=config,
        chunker=CharacterChunker(
            chunk_size=config.ingestion_chunk_size_chars_default,
            chunk_overlap=config.ingestion_chunk_overlap_chars_default,
        ),
        indexer=IndexerService(embedding_provider, vector_store),
    )
    file_ingestion_use_case = FileIngestionUseCase(
        config=config,
        parser=LocalFileDocumentParser(),
        ingestion_use_case=ingestion_use_case,
    )
    retrieval_use_case = RetrievalUseCase(
        config=config,
        retriever=RetrieverService(embedding_provider, vector_store),
    )
    generation_use_case = GenerationUseCase(
        config=config,
        retriever=RetrieverService(embedding_provider, vector_store),
        generator=GeneratorService(
            DeterministicLLMProvider(),
            insufficient_context_answer=config.insufficient_context_answer,
        ),
    )

    index_result = file_ingestion_use_case.execute(
        {
            "path": str(file_path),
            "document_id": "doc-refund-file",
            "index_name": "enterprise-kb",
            "metadata": {"language": "en", "tags": ["refund"]},
        }
    )
    retrieval_result = retrieval_use_case.execute(
        {
            "query": "How long can customers request a refund?",
            "index_name": "enterprise-kb",
            "filters": {"tags": ["refund"]},
        }
    )
    generation_result = generation_use_case.execute(
        {
            "question": "How long can customers request a refund?",
            "retrieval_request": {
                "index_name": "enterprise-kb",
                "filters": {"tags": ["refund"]},
            },
        }
    )

    assert index_result.status == "indexed"
    assert retrieval_result.chunks
    assert any(chunk.document_id == "doc-refund-file" for chunk in retrieval_result.chunks)
    assert generation_result.grounded is True
    assert generation_result.insufficient_context is False
    assert "7 days" in generation_result.answer
    assert set(generation_result.citations).issubset(
        {chunk.chunk_id for chunk in generation_result.used_chunks}
    )


def test_html_file_ingestion_supports_retrieve_and_generate_flow(tmp_path: Path) -> None:
    file_path = tmp_path / "refund-policy.html"
    file_path.write_text(
        (
            "<html><head><title>Refund policy</title></head><body>"
            "<h1>Refund policy</h1>"
            "<p>Customers can request a refund within 7 days from the payment date.</p>"
            "<p>Requests must be submitted through the official support portal.</p>"
            "</body></html>"
        ),
        encoding="utf-8",
    )

    config = RuntimeConfig()
    vector_store = InMemoryVectorStore()
    embedding_provider = HashEmbeddingProvider()
    ingestion_use_case = IngestionUseCase(
        config=config,
        chunker=CharacterChunker(
            chunk_size=config.ingestion_chunk_size_chars_default,
            chunk_overlap=config.ingestion_chunk_overlap_chars_default,
        ),
        indexer=IndexerService(embedding_provider, vector_store),
    )
    file_ingestion_use_case = FileIngestionUseCase(
        config=config,
        parser=LocalFileDocumentParser(),
        ingestion_use_case=ingestion_use_case,
    )
    retrieval_use_case = RetrievalUseCase(
        config=config,
        retriever=RetrieverService(embedding_provider, vector_store),
    )
    generation_use_case = GenerationUseCase(
        config=config,
        retriever=RetrieverService(embedding_provider, vector_store),
        generator=GeneratorService(
            DeterministicLLMProvider(),
            insufficient_context_answer=config.insufficient_context_answer,
        ),
    )

    index_result = file_ingestion_use_case.execute(
        {
            "path": str(file_path),
            "document_id": "doc-refund-html",
            "index_name": "enterprise-kb",
            "metadata": {"language": "en", "tags": ["refund"]},
        }
    )
    retrieval_result = retrieval_use_case.execute(
        {
            "query": "How long can customers request a refund?",
            "index_name": "enterprise-kb",
            "filters": {"source_type": "html", "tags": ["refund"]},
        }
    )
    generation_result = generation_use_case.execute(
        {
            "question": "How long can customers request a refund?",
            "retrieval_request": {
                "index_name": "enterprise-kb",
                "filters": {"source_type": "html", "tags": ["refund"]},
            },
        }
    )

    assert index_result.status == "indexed"
    assert retrieval_result.chunks
    assert any(chunk.document_id == "doc-refund-html" for chunk in retrieval_result.chunks)
    assert all(chunk.metadata["source_type"] == "html" for chunk in retrieval_result.chunks)
    assert generation_result.grounded is True
    assert generation_result.insufficient_context is False
    assert "7 days" in generation_result.answer
    assert set(generation_result.citations).issubset(
        {chunk.chunk_id for chunk in generation_result.used_chunks}
    )


def test_pdf_file_ingestion_supports_retrieve_and_generate_flow(tmp_path: Path) -> None:
    if shutil.which("ps2pdf") is None or shutil.which("pdftotext") is None:
        pytest.skip("pdf tools are not available")

    file_path = _build_simple_pdf(
        tmp_path,
        "refund-policy.pdf",
        [
            "Customers can request a refund within 7 days from the payment date.",
            "Requests must be submitted through the official support portal.",
        ],
    )

    config = RuntimeConfig()
    vector_store = InMemoryVectorStore()
    embedding_provider = HashEmbeddingProvider()
    ingestion_use_case = IngestionUseCase(
        config=config,
        chunker=CharacterChunker(
            chunk_size=config.ingestion_chunk_size_chars_default,
            chunk_overlap=config.ingestion_chunk_overlap_chars_default,
        ),
        indexer=IndexerService(embedding_provider, vector_store),
    )
    file_ingestion_use_case = FileIngestionUseCase(
        config=config,
        parser=LocalFileDocumentParser(),
        ingestion_use_case=ingestion_use_case,
    )
    retrieval_use_case = RetrievalUseCase(
        config=config,
        retriever=RetrieverService(embedding_provider, vector_store),
    )
    generation_use_case = GenerationUseCase(
        config=config,
        retriever=RetrieverService(embedding_provider, vector_store),
        generator=GeneratorService(
            DeterministicLLMProvider(),
            insufficient_context_answer=config.insufficient_context_answer,
        ),
    )

    index_result = file_ingestion_use_case.execute(
        {
            "path": str(file_path),
            "document_id": "doc-refund-pdf",
            "index_name": "enterprise-kb",
            "metadata": {"language": "en", "tags": ["refund"]},
        }
    )
    retrieval_result = retrieval_use_case.execute(
        {
            "query": "How long can customers request a refund?",
            "index_name": "enterprise-kb",
            "filters": {"source_type": "pdf", "tags": ["refund"]},
        }
    )
    generation_result = generation_use_case.execute(
        {
            "question": "How long can customers request a refund?",
            "retrieval_request": {
                "index_name": "enterprise-kb",
                "filters": {"source_type": "pdf", "tags": ["refund"]},
            },
        }
    )

    assert index_result.status == "indexed"
    assert retrieval_result.chunks
    assert any(chunk.document_id == "doc-refund-pdf" for chunk in retrieval_result.chunks)
    assert all(chunk.metadata["source_type"] == "pdf" for chunk in retrieval_result.chunks)
    assert generation_result.grounded is True
    assert generation_result.insufficient_context is False
    assert "7 days" in generation_result.answer
    assert set(generation_result.citations).issubset(
        {chunk.chunk_id for chunk in generation_result.used_chunks}
    )


def _build_simple_pdf(tmp_path: Path, filename: str, lines: list[str]) -> Path:
    ps_path = tmp_path / f"{filename}.ps"
    pdf_path = tmp_path / filename
    ps_lines = ["%!PS-Adobe-3.0", "/Times-Roman findfont 12 scalefont setfont"]
    y = 720
    for line in lines:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        ps_lines.append(f"72 {y} moveto")
        ps_lines.append(f"({escaped}) show")
        y -= 20
    ps_lines.append("showpage")
    ps_path.write_text("\n".join(ps_lines) + "\n", encoding="utf-8")
    subprocess.run(
        ["ps2pdf", str(ps_path), str(pdf_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return pdf_path
