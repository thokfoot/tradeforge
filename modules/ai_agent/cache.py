from __future__ import annotations

import threading
import time
from typing import Optional


class TtlCache:
    """TTL cache backed by Redis when available, otherwise in-process memory.

    Redis failures never break callers — they degrade to the in-memory store.
    """

    def __init__(self, ttl_seconds: int = 86400, redis_url: str = ""):
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._mem: dict[str, tuple[float, str]] = {}
        self._redis = None
        if redis_url:
            try:
                import redis  # type: ignore

                self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    def get(self, key: str) -> Optional[str]:
        if self._redis is not None:
            try:
                return self._redis.get(key)
            except Exception:
                return self._mem_get(key)
        return self._mem_get(key)

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds or self._ttl
        if self._redis is not None:
            try:
                self._redis.setex(key, ttl, value)
                return
            except Exception:
                pass
        with self._lock:
            self._mem[key] = (time.time() + ttl, value)

    def _mem_get(self, key: str) -> Optional[str]:
        with self._lock:
            item = self._mem.get(key)
            if item is None:
                return None
            expires, value = item
            if time.time() > expires:
                self._mem.pop(key, None)
                return None
            return value
