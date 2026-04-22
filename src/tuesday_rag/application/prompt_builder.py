from tuesday_rag.domain.models import RetrievedChunk


def build_grounded_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    context = "\n".join(f"[{chunk.chunk_id}] {chunk.text}" for chunk in chunks)
    return (
        "Bạn là trợ lý trả lời chỉ dựa trên context được cung cấp.\n"
        "Không được khẳng định điều không xuất hiện trong context.\n"
        f"Câu hỏi: {question}\n"
        "Context:\n"
        f"{context}\n"
        "Nếu context không đủ, phải nói rõ không đủ dữ liệu.\n"
        "Mọi viện dẫn phải dùng chunk_id."
    )
