from tuesday_rag.domain.models import RetrievedChunk
from tuesday_rag.generation.prompt_builder import build_grounded_prompt


def test_prompt_builder_creates_deterministic_grounded_prompt() -> None:
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-doc-001-0001",
            document_id="doc-001",
            text="Khach hang co the yeu cau hoan tien trong vong 7 ngay.",
            score=0.92,
            metadata={"chunk_id": "chunk-doc-001-0001"},
        ),
        RetrievedChunk(
            chunk_id="chunk-doc-001-0002",
            document_id="doc-001",
            text="Yeu cau hoan tien phai duoc gui qua cong ho tro chinh thuc.",
            score=0.81,
            metadata={"chunk_id": "chunk-doc-001-0002"},
        ),
    ]

    prompt = build_grounded_prompt("Khach hang duoc hoan tien trong bao lau?", chunks)

    assert "You are an assistant that answers only from the provided context." in prompt
    assert "Question: Khach hang duoc hoan tien trong bao lau?" in prompt
    assert "[chunk-doc-001-0001] Khach hang co the yeu cau hoan tien trong vong 7 ngay." in prompt
    assert (
        "[chunk-doc-001-0002] Yeu cau hoan tien phai duoc gui qua cong ho tro chinh thuc."
        in prompt
    )
    assert (
        "If the context is insufficient, explicitly say there is not enough information."
        in prompt
    )
    assert "All citations must use chunk_id." in prompt
