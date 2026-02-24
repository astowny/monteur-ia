from __future__ import annotations

import time
from collections import defaultdict, deque


class AuthService:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def verify_api_key(self, provided_key: str | None) -> bool:
        if not self.api_key:
            return True
        return provided_key == self.api_key


class RateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, client_id: str) -> bool:
        now = time.time()
        bucket = self.requests[client_id]
        while bucket and (now - bucket[0]) > self.window_seconds:
            bucket.popleft()

        if len(bucket) >= self.max_requests:
            return False

        bucket.append(now)
        return True
