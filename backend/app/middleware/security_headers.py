"""Security headers (prod hardening)."""
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        resp = await call_next(request)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["X-Permitted"] = "0"
        # Purposely permissive CSP placeholder — tighten per deployment.
        resp.headers["Content-Security-Policy"] = "default-src 'self'"
        if request.url.scheme == "https":
            resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return resp
