"""Rate limiting + abuse guard (in-memory, single-instance safe).

In production use Redis-backed limiter (shared across instances). This guard
blocks login/brute-force bursts, webhook floods, and API abuse without
blocking legitimate customers (generous per-IP buckets + global counters).

Usage: register middleware in main.py. Headers: X-RateLimit-Remaining.
"""
import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# path prefix -> (requests, window_seconds, max)
LIMITS: list[tuple[str, int, int]] = [
    ("/api/v1/auth/login", 60, 20),
    ("/api/v1/auth/register", 60, 20),
    ("/api/v1/payments/webhook", 60, 30),
    ("/api/v1/", 60, 300),
]

_buckets: dict[str, list[float]] = defaultdict(list)


def _client_key(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    ip = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "unknown")
    return ip


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only enforce in prod. Dev/tests use generous traffic and would flake
        # on shared-bucket limits. Set ENV=prod to enable.
        from app.config import settings
        if settings.ENV != "prod":
            return await call_next(request)
        path = request.url.path
        limit = next(((p, w, m) for p, w, m in LIMITS if path.startswith(p)), None)
        if limit is not None:
            prefix, window, mx = limit
            key = _client_key(request) + ":" + prefix
            now = time.time()
            q = _buckets[key]
            _buckets[key] = [t for t in q if now - t < window]
            if len(_buckets[key]) >= mx:
                return JSONResponse({"detail": "Too many requests. Try again shortly."}, status_code=429)
            _buckets[key].append(now)
        return await call_next(request)
