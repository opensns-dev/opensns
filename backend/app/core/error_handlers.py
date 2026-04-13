"""
Centralized error handling middleware for OpenSNS API.
Converts all exceptions to consistent JSON responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError as PydanticValidationError
from app.core.exceptions import (
    OpenSNSError,
    EngineNotFoundError,
    APIKeyNotConfiguredError,
    GenerationError,
    ImageGenerationError,
    VideoGenerationError,
    WorkflowError,
    ResearchError,
)
import logging

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format."""

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 500,
        details: dict = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status_code,
            content={
                "error": {
                    "code": self.error_code,
                    "message": self.message,
                    "details": self.details,
                }
            },
        )


async def opensns_exception_handler(request: Request, exc: OpenSNSError):
    """Handle all OpenSNS custom exceptions."""
    logger.warning(f"OpenSNS error: {exc}", exc_info=True)

    if isinstance(exc, EngineNotFoundError):
        return ErrorResponse(
            error_code="ENGINE_NOT_FOUND",
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "engine_type": exc.engine_type,
                "requested": exc.name,
                "available": exc.available,
            },
        ).to_response()

    if isinstance(exc, APIKeyNotConfiguredError):
        return ErrorResponse(
            error_code="API_KEY_MISSING",
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"service": exc.service},
        ).to_response()

    if isinstance(exc, ImageGenerationError):
        return ErrorResponse(
            error_code="IMAGE_GENERATION_FAILED",
            message=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ).to_response()

    if isinstance(exc, VideoGenerationError):
        return ErrorResponse(
            error_code="VIDEO_GENERATION_FAILED",
            message=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ).to_response()

    if isinstance(exc, GenerationError):
        return ErrorResponse(
            error_code="GENERATION_FAILED",
            message=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ).to_response()

    if isinstance(exc, WorkflowError):
        return ErrorResponse(
            error_code="WORKFLOW_ERROR",
            message=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ).to_response()

    if isinstance(exc, ResearchError):
        return ErrorResponse(
            error_code="RESEARCH_ERROR",
            message=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ).to_response()

    # Fallback for any OpenSNSError
    return ErrorResponse(
        error_code="OPENSNS_ERROR",
        message=str(exc),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    ).to_response()


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors (duplicate keys, FK violations)."""
    logger.warning(f"Database integrity error: {exc}", exc_info=True)

    # Extract useful info from the error
    error_str = str(exc.orig) if exc.orig else str(exc)

    if "UNIQUE constraint" in error_str or "duplicate key" in error_str.lower():
        return ErrorResponse(
            error_code="DUPLICATE_ENTRY",
            message="A record with this value already exists",
            status_code=status.HTTP_409_CONFLICT,
        ).to_response()

    if "FOREIGN KEY constraint" in error_str or "foreign key" in error_str.lower():
        return ErrorResponse(
            error_code="REFERENCE_ERROR",
            message="Referenced record does not exist",
            status_code=status.HTTP_400_BAD_REQUEST,
        ).to_response()

    return ErrorResponse(
        error_code="DATABASE_ERROR",
        message="A database constraint was violated",
        status_code=status.HTTP_400_BAD_REQUEST,
    ).to_response()


async def pydantic_validation_handler(request: Request, exc: PydanticValidationError):
    """Handle Pydantic validation errors with detailed field info."""
    logger.info(f"Validation error: {exc.error_count()} errors")

    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return ErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": errors},
    ).to_response()


async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return ErrorResponse(
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    ).to_response()


def register_error_handlers(app):
    """Register all error handlers with the FastAPI app."""
    from pydantic import ValidationError as PydanticValidationError

    app.add_exception_handler(OpenSNSError, opensns_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_handler)
    # Generic exception handler: catches unhandled errors in production
    # Disabled in DEBUG mode to preserve stack traces for development
    from app.core.config import settings

    if not settings.DEBUG:
        app.add_exception_handler(Exception, generic_exception_handler)
