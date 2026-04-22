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

NO_MATCH_QUERY = "Ve tinh quy dao can hieu chuan quang pho dinh ky khong?"
