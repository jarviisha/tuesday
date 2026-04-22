import argparse
import asyncio

import httpx

REFUND_DOCUMENT = {
    "document_id": "doc-refund-001",
    "title": "Chinh sach hoan tien",
    "content": (
        "Khach hang co the yeu cau hoan tien trong vong 7 ngay ke tu ngay thanh toan. "
        "Yeu cau hoan tien phai duoc gui qua cong ho tro chinh thuc."
    ),
    "source_type": "text",
    "source_uri": "internal://policy/refund",
    "index_name": "enterprise-kb",
    "metadata": {
        "language": "vi",
        "tags": ["policy", "refund"],
    },
}


async def _run_in_process() -> None:
    from tuesday_rag.api.app import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await _run_flow(client)


async def _run_remote(base_url: str) -> None:
    async with httpx.AsyncClient(base_url=base_url) as client:
        await _run_flow(client)


async def _run_flow(client: httpx.AsyncClient) -> None:
    index_response = await client.post("/documents/index", json=REFUND_DOCUMENT)
    index_response.raise_for_status()

    retrieve_response = await client.post(
        "/retrieve",
        json={
            "query": "Khach hang duoc hoan tien trong bao lau?",
            "index_name": "enterprise-kb",
        },
    )
    retrieve_response.raise_for_status()
    if not retrieve_response.json()["chunks"]:
        raise RuntimeError("smoke test failed: retrieve returned no chunks")

    generate_response = await client.post(
        "/generate",
        json={
            "question": "Khach hang duoc hoan tien trong bao lau?",
            "retrieval_request": {
                "filters": {"tags": ["refund"]},
                "index_name": "enterprise-kb",
            },
        },
    )
    generate_response.raise_for_status()
    body = generate_response.json()
    if not body["grounded"] or body["insufficient_context"] or not body["citations"]:
        raise RuntimeError("smoke test failed: generate response did not stay grounded")
    print("smoke test passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url")
    args = parser.parse_args()
    if args.base_url:
        asyncio.run(_run_remote(args.base_url))
        return
    asyncio.run(_run_in_process())


if __name__ == "__main__":
    main()
