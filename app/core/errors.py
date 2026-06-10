from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, NoResultFound


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _error_payload(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message}}


def _code_for_status(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    return mapping.get(status_code, "ERROR")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_error_payload(_code_for_status(exc.status_code), exc.message))

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(status_code=exc.status_code, content=_error_payload(_code_for_status(exc.status_code), detail))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        message = "; ".join(error.get("msg", "Invalid input") for error in exc.errors()) or "Validation failed"
        return JSONResponse(status_code=422, content=_error_payload("VALIDATION_ERROR", message))

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_: Request, __: IntegrityError) -> JSONResponse:
        return JSONResponse(status_code=409, content=_error_payload("CONFLICT", "Database constraint violated"))

    @app.exception_handler(NoResultFound)
    async def not_found_handler(_: Request, __: NoResultFound) -> JSONResponse:
        return JSONResponse(status_code=404, content=_error_payload("NOT_FOUND", "Resource not found"))

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content=_error_payload("INTERNAL_SERVER_ERROR", "An unexpected error occurred"))
