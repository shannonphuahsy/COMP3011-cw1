# app/core/limiter.py

from starlette.responses import JSONResponse

ENABLED = True

try:
    # Real SlowAPI
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["60/minute"]
    )

    async def _rate_limit_exceeded_handler(request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

except Exception:
    ENABLED = False

    class _NoopLimiter:
        def limit(self, *_args, **_kwargs):
            def decorator(fn):
                return fn
            return decorator

    limiter = _NoopLimiter()

    async def _rate_limit_exceeded_handler(request, exc):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded (fallback)"}
        )

    class SlowAPIMiddleware:
        def __init__(self, app, *args, **kwargs):
            self.app = app

        async def __call__(self, scope, receive, send):
            await self.app(scope, receive, send)