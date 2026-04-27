"""Global error handling for FastAPI.

WP-1.1: Catches all exceptions and returns a consistent JSON error envelope.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def _error_response(status_code: int, code: str, message: str, detail=None) -> JSONResponse:
    body: dict = {"error": {"code": code, "message": message}}
    if detail is not None:
        body["error"]["detail"] = detail
    return JSONResponse(status_code=status_code, content=body)


def register_error_handlers(app: FastAPI) -> None:
    """Attach exception handlers to the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning("HTTP %s: %s", exc.status_code, exc.detail)
        return _error_response(exc.status_code, f"HTTP_{exc.status_code}", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation error: %s", exc.errors())
        return _error_response(422, "VALIDATION_ERROR", "Request validation failed", exc.errors())

    # Anthropic SDK errors — imported lazily to avoid hard dependency at import time
    try:
        import anthropic

        @app.exception_handler(anthropic.RateLimitError)
        async def rate_limit_handler(request: Request, exc: anthropic.RateLimitError):
            logger.error("Anthropic rate limit: %s", exc, exc_info=True)
            return _error_response(503, "RATE_LIMIT", "AI service rate limited, please retry later")

        @app.exception_handler(anthropic.APIConnectionError)
        async def connection_error_handler(request: Request, exc: anthropic.APIConnectionError):
            logger.error("Anthropic connection error: %s", exc, exc_info=True)
            return _error_response(503, "SERVICE_UNAVAILABLE", "AI service temporarily unavailable")

        @app.exception_handler(anthropic.APIStatusError)
        async def api_status_handler(request: Request, exc: anthropic.APIStatusError):
            logger.error("Anthropic API error %s: %s", exc.status_code, exc, exc_info=True)
            return _error_response(503, "AI_SERVICE_ERROR", "AI service error")

    except ImportError:
        pass  # anthropic not installed — skip these handlers

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return _error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
