import asyncio
import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.db.init_db import init_db
from app.services.response_envelope import success_response


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version="1.0.0",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.on_event("startup")
    def on_startup() -> None:
        try:
            init_db()
        except Exception as e:
            logging.exception("Error during startup: %s", e)

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, Any]:
        return success_response({"status": "ok"}, "Health check ok")

    @app.get("/", tags=["root"])
    def root() -> dict[str, Any]:
        return success_response({"message": "MM Motors API", "version": "1.0.0"}, "MM Motors API")

    return app


app = create_app()
