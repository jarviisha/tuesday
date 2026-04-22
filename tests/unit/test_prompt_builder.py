from tuesday_rag.application.prompt_builder import build_grounded_prompt
from tuesday_rag.domain.models import RetrievedChunk


def test_prompt_builder_creates_deterministic_grounded_prompt() -> None:
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-doc-001-0001",
            document_id="doc-001",
            text="Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày.",
            score=0.92,
            metadata={"chunk_id": "chunk-doc-001-0001"},
        ),
        RetrievedChunk(
            chunk_id="chunk-doc-001-0002",
            document_id="doc-001",
            text="Yêu cầu hoàn tiền cần gửi qua cổng hỗ trợ chính thức.",
            score=0.81,
            metadata={"chunk_id": "chunk-doc-001-0002"},
        ),
    ]

    prompt = build_grounded_prompt("Khách hàng được hoàn tiền trong bao lâu?", chunks)

    assert "Bạn là trợ lý trả lời chỉ dựa trên context được cung cấp." in prompt
    assert "Câu hỏi: Khách hàng được hoàn tiền trong bao lâu?" in prompt
    assert "[chunk-doc-001-0001] Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày." in prompt
    assert "[chunk-doc-001-0002] Yêu cầu hoàn tiền cần gửi qua cổng hỗ trợ chính thức." in prompt
    assert "Nếu context không đủ, phải nói rõ không đủ dữ liệu." in prompt
    assert "Mọi viện dẫn phải dùng chunk_id." in prompt
