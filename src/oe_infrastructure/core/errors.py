"""Structured API errors."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status


class AppError(Exception):
    """Base application error carrying an HTTP status and a machine code."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "app_error",
        http_status: int = status.HTTP_400_BAD_REQUEST,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.details = details

    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=self.http_status,
            detail={
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        )


class NotFoundError(AppError):
    def __init__(
        self,
        resource: str,
        resource_id: str | None = None,
        *,
        code: str = "not_found",
    ) -> None:
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} '{resource_id}' not found"
        super().__init__(message, code=code, http_status=status.HTTP_404_NOT_FOUND)


class ConflictError(AppError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "conflict",
        details: Any = None,
    ) -> None:
        super().__init__(
            message,
            code=code,
            http_status=status.HTTP_409_CONFLICT,
            details=details,
        )


class ValidationFailure(AppError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "validation_error",
        details: Any = None,
    ) -> None:
        super().__init__(
            message,
            code=code,
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class UnauthorizedError(AppError):
    def __init__(
        self,
        message: str = "Authentication required",
        *,
        code: str = "unauthorized",
    ) -> None:
        super().__init__(message, code=code, http_status=status.HTTP_401_UNAUTHORIZED)


class PermissionDeniedError(AppError):
    def __init__(
        self,
        message: str = "Insufficient permissions",
        *,
        code: str = "permission_denied",
    ) -> None:
        super().__init__(message, code=code, http_status=status.HTTP_403_FORBIDDEN)


class RateLimitedError(AppError):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        code: str = "rate_limited",
        retry_after_seconds: int | None = None,
    ) -> None:
        details = {"retry_after_seconds": retry_after_seconds}
        super().__init__(
            message,
            code=code,
            http_status=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )