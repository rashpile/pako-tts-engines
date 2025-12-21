"""Error handling middleware."""

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.models.errors import APIError, ErrorCode, ErrorDetail, ErrorResponse

logger = structlog.get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling API errors."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Handle request and catch any API errors.

        Args:
            request: Incoming request.
            call_next: Next middleware/handler.

        Returns:
            Response from handler or error response.
        """
        try:
            return await call_next(request)
        except APIError as e:
            logger.warning(
                "api.error",
                error_code=e.code.value,
                message=e.message,
                details=e.details,
                path=request.url.path,
                method=request.method,
            )
            return JSONResponse(
                status_code=e.status_code,
                content=e.to_response().model_dump(),
            )
        except Exception as e:
            logger.exception(
                "api.unhandled_error",
                error_type=type(e).__name__,
                message=str(e),
                path=request.url.path,
                method=request.method,
            )
            error_response = ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.SYNTHESIS_FAILED,
                    message="An internal error occurred",
                    details=None,
                )
            )
            return JSONResponse(
                status_code=500,
                content=error_response.model_dump(),
            )
