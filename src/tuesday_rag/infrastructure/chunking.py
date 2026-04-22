from tuesday_rag.domain.errors import ChunkingError
from tuesday_rag.domain.models import Chunk, SourceDocument


class CharacterChunker:
    def __init__(self, *, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk(self, document: SourceDocument) -> list[Chunk]:
        if not document.content:
            raise ChunkingError("Document content is empty")
        chunks: list[Chunk] = []
        start = 0
        sequence_no = 1
        while start < len(document.content):
            end = min(start + self._chunk_size, len(document.content))
            text = document.content[start:end].strip()
            if text:
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
                        char_start=start,
                        char_end=end,
                        metadata=metadata,
                    )
                )
            if end == len(document.content):
                break
            start = end - self._chunk_overlap
            sequence_no += 1
        return chunks
