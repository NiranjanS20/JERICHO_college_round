"""
Rate limiting configuration using slowapi.
"""
from __future__ import annotations
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    HAS_SLOWAPI = True
except ImportError:
    HAS_SLOWAPI = False

    class RateLimitExceeded(Exception):
        pass

    class DummyLimiter:
        def __init__(self, key_func=None):
            self.key_func = key_func

        def limit(self, limit_value: str):
            def decorator(func):
                return func
            return decorator

    Limiter = DummyLimiter  # type: ignore

    def get_remote_address(request: Request) -> str:
        return request.client.host if request.client else "127.0.0.1"

    def _rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
        return Response("Rate limit exceeded", status_code=429)

from fastapi import FastAPI, Request, Response

limiter = Limiter(key_func=get_remote_address)

def setup_rate_limiting(app: FastAPI) -> None:
    """Attach rate limiter to the FastAPI app."""
    app.state.limiter = limiter
    if HAS_SLOWAPI:
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

