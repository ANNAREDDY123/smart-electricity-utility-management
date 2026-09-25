import logging
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


logger = logging.getLogger(__name__)


def make_json_safe(value: Any) -> Any:
    """
    Convert values that are not directly JSON serializable
    into safe JSON-compatible values.
    """

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Exception):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            make_json_safe(item)
            for item in value
        ]

    return str(value)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    safe_errors = make_json_safe(
        exc.errors()
    )

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": safe_errors,
        },
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
):
    logger.exception(
        "Database integrity error: %s",
        exc,
    )

    return JSONResponse(
        status_code=409,
        content={
            "detail": "Database integrity constraint violated",
        },
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
):
    logger.exception(
        "Database error: %s",
        exc,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Database operation failed",
        },
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Unhandled application error: %s",
        exc,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
        },
    )