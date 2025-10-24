from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# NOTE: Demo only — real impl should use Redis/DB to store keys
_seen_keys: set[str] = set()


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        key = request.headers.get('Idempotency-Key')
        if key and key in _seen_keys:
            return Response(status_code=208)  # Already Reported
        if key:
            _seen_keys.add(key)
        return await call_next(request)
