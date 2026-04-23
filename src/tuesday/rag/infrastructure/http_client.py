import json
from urllib import request
from urllib.error import HTTPError, URLError


def post_json(
    *,
    url: str,
    headers: dict[str, str],
    payload: dict,
    timeout_seconds: float = 30.0,
) -> dict:
    raw_request = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **headers,
        },
        method="POST",
    )
    try:
        with request.urlopen(raw_request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("provider request failed") from exc
