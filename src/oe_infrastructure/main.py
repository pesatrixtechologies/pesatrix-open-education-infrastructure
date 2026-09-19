"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from oe_infrastructure import __version__
from oe_infrastructure.api import api_router
from oe_infrastructure.config import get_settings
from oe_infrastructure.core.errors import AppError
from oe_infrastructure.database import dispose_engine, SessionLocal
from oe_infrastructure.services.bootstrap import bootstrap_admin

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if not settings.is_production:
        from oe_infrastructure.database import init_schema

        await init_schema()
        async with SessionLocal() as session:
            await bootstrap_admin(session)
            await session.commit()
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="PESATRIX Open Education Infrastructure API",
        version=__version__,
        description=(
            "Reusable, secure, interoperable digital infrastructure for "
            "structured educational events and information in low-resource "
            "environments. No personal data is stored by this system."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list() or ["*"],
        allow_credentials=not (settings.cors_origin_list() == []),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        response = exc.to_http_exception()
        return JSONResponse(content=response.detail, status_code=exc.http_status)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "openapi": "/openapi.json",
        }

    app.include_router(api_router)
    return app


app = create_app()