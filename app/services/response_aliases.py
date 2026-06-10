from __future__ import annotations

from collections.abc import Mapping


def _camelize(key: str) -> str:
    if "_" not in key:
        return key
    parts = key.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def with_response_aliases(value):
    if isinstance(value, list):
        return [with_response_aliases(item) for item in value]
    if isinstance(value, tuple):
        return tuple(with_response_aliases(item) for item in value)
    if not isinstance(value, Mapping):
        return value

    payload = {}
    for key, item in value.items():
        next_value = with_response_aliases(item)
        payload[key] = next_value
        if isinstance(key, str):
            alias = _camelize(key)
            if alias != key and alias not in payload:
                payload[alias] = next_value
    return payload
