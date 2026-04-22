from dataclasses import dataclass

NO_MATCH_QUERY = "Ve tinh quy dao can hieu chuan quang pho dinh ky khong?"

REFUND_DOCUMENT = {
    "document_id": "doc-refund-001",
    "title": "Chinh sach hoan tien",
    "content": (
        "Khach hang co the yeu cau hoan tien trong vong 7 ngay ke tu ngay thanh toan. "
        "Yeu cau hoan tien phai duoc gui qua cong ho tro chinh thuc."
    ),
    "source_type": "text",
    "source_uri": "internal://policy/refund",
    "metadata": {
        "language": "vi",
        "tags": ["policy", "refund"],
    },
    "index_name": "enterprise-kb",
}

ONBOARDING_DOCUMENT = {
    "document_id": "doc-onboarding-001",
    "title": "Huong dan onboarding nhan su",
    "content": " ".join(
        [
            "Nhan su moi phai hoan tat giay to trong 3 ngay dau tien.",
            "Tai khoan email noi bo duoc cap trong ngay lam viec dau tien.",
            "Quan ly truc tiep phai sap xep buoi gioi thieu voi ca nhom.",
        ]
        * 120
    ),
    "source_type": "text",
    "source_uri": "internal://hr/onboarding",
    "metadata": {
        "language": "vi",
        "tags": ["hr", "onboarding"],
    },
    "index_name": "enterprise-kb",
}


@dataclass(frozen=True)
class RetrievalGoldenCase:
    case_id: str
    query: str
    index_name: str
    filters: dict | None
    expected_document_ids: list[str]
    expected_empty: bool
    behavior: str


@dataclass(frozen=True)
class GenerationGoldenCase:
    case_id: str
    question: str
    index_name: str
    retrieval_request: dict
    expected_insufficient_context: bool
    expected_grounded: bool
    expected_answer_substring: str | None
    behavior: str


RETRIEVAL_GOLDEN_CASES = [
    RetrievalGoldenCase(
        case_id="retrieval_refund_match",
        query="Khach hang duoc hoan tien trong bao lau?",
        index_name="enterprise-kb",
        filters={"language": "vi", "tags": ["refund"]},
        expected_document_ids=["doc-refund-001"],
        expected_empty=False,
        behavior="retrieval_match_contains_expected_document",
    ),
    RetrievalGoldenCase(
        case_id="retrieval_no_match",
        query=NO_MATCH_QUERY,
        index_name="enterprise-kb",
        filters=None,
        expected_document_ids=[],
        expected_empty=True,
        behavior="retrieval_returns_empty_for_no_match",
    ),
]


GENERATION_GOLDEN_CASES = [
    GenerationGoldenCase(
        case_id="generation_grounded_refund",
        question="Khach hang duoc hoan tien trong bao lau?",
        index_name="enterprise-kb",
        retrieval_request={"filters": {"tags": ["refund"]}},
        expected_insufficient_context=False,
        expected_grounded=True,
        expected_answer_substring="7 ngay",
        behavior="generation_returns_grounded_answer_with_valid_citations",
    ),
    GenerationGoldenCase(
        case_id="generation_insufficient_context",
        question=NO_MATCH_QUERY,
        index_name="enterprise-kb",
        retrieval_request={},
        expected_insufficient_context=True,
        expected_grounded=False,
        expected_answer_substring=None,
        behavior="generation_returns_insufficient_context_without_citations",
    ),
]
