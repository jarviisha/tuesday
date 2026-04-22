REFUND_DOCUMENT = {
    "document_id": "doc-refund-001",
    "title": "Chính sách hoàn tiền",
    "content": (
        "Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày kể từ ngày thanh toán. "
        "Yêu cầu hoàn tiền cần gửi qua cổng hỗ trợ chính thức."
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
    "title": "Hướng dẫn onboarding nhân sự",
    "content": " ".join(
        [
            "Nhân sự mới cần hoàn tất hồ sơ trong 3 ngày đầu.",
            "Tài khoản email nội bộ được cấp trong ngày làm việc đầu tiên.",
            "Quản lý trực tiếp cần lên lịch buổi giới thiệu đội nhóm.",
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

NO_MATCH_QUERY = "Vệ tinh quỹ đạo có cần hiệu chuẩn quang phổ định kỳ không?"
