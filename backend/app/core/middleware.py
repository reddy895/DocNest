import time
import uuid
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("docnest.middleware")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that attaches a unique X-Request-ID to every incoming HTTP request,
    measures precise millisecond latency, and logs structured telemetry.
    """

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = req_id
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Response-Time-MS"] = str(duration_ms)

            if request.url.path.startswith("/api/"):
                logger.info(
                    f"[{req_id}] {request.method} {request.url.path} -> HTTP {response.status_code} ({duration_ms}ms)"
                )
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"[{req_id}] FAILED {request.method} {request.url.path} after {duration_ms}ms: {exc}",
                exc_info=True,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": True,
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "Internal Server Error. Please inspect server logs.",
                    "request_id": req_id,
                    "path": request.url.path,
                },
                headers={"X-Request-ID": req_id, "X-Response-Time-MS": str(duration_ms)},
            )


def register_error_handlers(app: FastAPI) -> None:
    """
    Register uniform structured JSON error handlers across the FastAPI application.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "status_code": exc.status_code,
                "message": exc.detail,
                "path": request.url.path,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": True,
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "Validation Error: invalid input parameters or schema.",
                "details": exc.errors(),
                "path": request.url.path,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error. Please inspect server logs or retry.",
                "path": request.url.path,
            },
        )
