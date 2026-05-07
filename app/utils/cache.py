import time
from typing import Any, Optional

_cache: dict = {}


def cache_set(key: str, value: Any, ttl_seconds: int = 60) -> None:
    _cache[key] = {"value": value, "expires": time.time() + ttl_seconds}


def cache_get(key: str) -> Optional[Any]:
    item = _cache.get(key)
    if item and item["expires"] > time.time():
        return item["value"]
    _cache.pop(key, None)
    return None


def cache_delete(key: str) -> None:
    _cache.pop(key, None)


def cache_clear_prefix(prefix: str) -> None:
    for key in [k for k in _cache if k.startswith(prefix)]:
        del _cache[key]
