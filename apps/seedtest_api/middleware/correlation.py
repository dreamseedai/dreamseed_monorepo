import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        cid = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        response: Response = await call_next(request)
        response.headers["x-correlation-id"] = cid
        return response


class CorrelationMiddleware(CorrelationIdMiddleware):
    pass
