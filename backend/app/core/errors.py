import logging
from http import HTTPStatus
import re

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _error_body(
    *,
    request: Request,
    status_code: int,
    message: str,
    code: str,
    detail,
):
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": _request_id(request),
            "status_code": status_code,
        },
        "detail": detail,
    }


def _error_headers(request: Request) -> dict[str, str]:
    request_id = _request_id(request)
    if not request_id:
        return {}
    return {"X-Request-ID": request_id}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        message = str(exc.detail)
        phrase = HTTPStatus(exc.status_code).phrase.upper().replace("'", "")
        code = re.sub(r"[^A-Z0-9]+", "_", phrase).strip("_")
        logger.warning(
            "http_exception path=%s method=%s status_code=%s request_id=%s detail=%s",
            request.url.path,
            request.method,
            exc.status_code,
            _request_id(request),
            message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            headers=_error_headers(request),
            content=_error_body(
                request=request,
                status_code=exc.status_code,
                message=message,
                code=code,
                detail=exc.detail,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(
            "validation_exception path=%s method=%s request_id=%s errors=%s",
            request.url.path,
            request.method,
            _request_id(request),
            exc.errors(),
        )
        return JSONResponse(
            status_code=422,
            headers=_error_headers(request),
            content=_error_body(
                request=request,
                status_code=422,
                message="Request validation failed",
                code="VALIDATION_ERROR",
                detail=exc.errors(),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "unhandled_exception path=%s method=%s request_id=%s",
            request.url.path,
            request.method,
            _request_id(request),
        )
        return JSONResponse(
            status_code=500,
            headers=_error_headers(request),
            content=_error_body(
                request=request,
                status_code=500,
                message="Internal server error",
                code="INTERNAL_SERVER_ERROR",
                detail="Internal server error",
            ),
        )
