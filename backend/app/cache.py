from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

from .config import settings

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


_redis_client: Optional["redis.Redis"] = None


def get_redis_client() -> Optional["redis.Redis"]:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not settings.REDIS_URL or not redis:
        return None
    _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def generate_cache_key(namespace: str, payload: dict[str, Any]) -> str:
    secret = settings.CACHE_KEY_SECRET or ""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256((serialized + secret).encode("utf-8")).hexdigest()
    return f"iv:{namespace}:{digest}"


