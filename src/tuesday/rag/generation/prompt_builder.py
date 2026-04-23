from tuesday.rag.domain.models import RetrievedChunk


def build_grounded_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    context = "\n".join(f"[{chunk.chunk_id}] {chunk.text}" for chunk in chunks)
    return (
        "You are an assistant that answers only from the provided context.\n"
        "Do not assert anything that does not appear in the context.\n"
        f"Question: {question}\n"
        "Context:\n"
        f"{context}\n"
        "If the context is insufficient, explicitly say there is not enough information.\n"
        "All citations must use chunk_id."
    )
