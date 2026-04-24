from llama_index.core.node_parser import SentenceSplitter

from tuesday.rag.domain.errors import ChunkingError
from tuesday.rag.domain.models import Chunk, SourceDocument


class LlamaIndexNodeParser:
    """Token-based chunker using LlamaIndex SentenceSplitter (supersedes DL-006)."""

    def __init__(self, *, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def chunk(self, document: SourceDocument) -> list[Chunk]:
        if not document.content:
            raise ChunkingError("Document content is empty")

        nodes = self._splitter.get_nodes_from_documents(
            [
                _source_to_llama_document(document)
            ]
        )

        chunks: list[Chunk] = []
        for sequence_no, node in enumerate(nodes, start=1):
            text = node.get_content().strip()
            if not text:
                continue
            chunk_id = f"chunk-{document.document_id}-{sequence_no:04d}"
            metadata = {
                "document_id": document.document_id,
                "chunk_id": chunk_id,
                "title": document.title,
                "source_type": document.source_type,
                "source_uri": document.source_uri,
                "sequence_no": sequence_no,
                "language": document.language,
                "tags": document.metadata.get("tags"),
                "version": document.metadata.get("version"),
            }
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    text=text,
                    sequence_no=sequence_no,
                    token_count=None,
                    char_start=None,
                    char_end=None,
                    metadata=metadata,
                )
            )
        return chunks


def _source_to_llama_document(doc: SourceDocument):
    from llama_index.core import Document as LlamaDocument

    return LlamaDocument(text=doc.content, doc_id=doc.document_id)
