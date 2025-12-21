"""Error codes and API error classes."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """API error codes."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    TEXT_TOO_LONG = "TEXT_TOO_LONG"
    TEXT_EMPTY = "TEXT_EMPTY"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    LANGUAGE_NOT_SUPPORTED = "LANGUAGE_NOT_SUPPORTED"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    SYNTHESIS_FAILED = "SYNTHESIS_FAILED"
    SERVICE_BUSY = "SERVICE_BUSY"
    SYNTHESIS_TIMEOUT = "SYNTHESIS_TIMEOUT"


ERROR_STATUS_CODES: dict[ErrorCode, int] = {
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.TEXT_TOO_LONG: 413,
    ErrorCode.TEXT_EMPTY: 422,
    ErrorCode.MODEL_NOT_FOUND: 404,
    ErrorCode.MODEL_UNAVAILABLE: 503,
    ErrorCode.LANGUAGE_NOT_SUPPORTED: 422,
    ErrorCode.INVALID_PARAMETER: 422,
    ErrorCode.SYNTHESIS_FAILED: 500,
    ErrorCode.SERVICE_BUSY: 503,
    ErrorCode.SYNTHESIS_TIMEOUT: 504,
}


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: ErrorCode = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """API error response wrapper."""

    error: ErrorDetail = Field(..., description="Error details")


class APIError(Exception):
    """API error exception."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)

    @property
    def status_code(self) -> int:
        """Get HTTP status code for this error."""
        return ERROR_STATUS_CODES.get(self.code, 500)

    def to_response(self) -> ErrorResponse:
        """Convert to API error response."""
        return ErrorResponse(
            error=ErrorDetail(
                code=self.code,
                message=self.message,
                details=self.details,
            )
        )
