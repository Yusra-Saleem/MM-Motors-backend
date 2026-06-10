from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.response_aliases import with_response_aliases


def success_response(data: Any = None, message: str = "OK") -> dict[str, Any]:
    payload: dict[str, Any] = {"success": True, "data": data, "message": message}
    if isinstance(data, Mapping):
        payload.update(with_response_aliases(dict(data)))
    elif isinstance(data, list):
        payload["data"] = [with_response_aliases(item) for item in data]
    return payload
