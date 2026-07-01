"""SmartEval AI - FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pathlib import Path

from smartevalai.api.v1.auth import router as auth_router
from smartevalai.api.v1.exams import router as exams_router
from smartevalai.api.v1.reports import router as reports_router
from smartevalai.api.v1.submissions import router as submissions_router
from smartevalai.core.config import get_settings
from smartevalai.core.deps import get_current_user
from smartevalai.core.logging import configure_logging
from smartevalai.models.user import User


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: runs once on startup and once on shutdown."""
    configure_logging()
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} in '{settings.environment}' mode")
    yield
    logger.info(f"Shutting down {settings.app_name}")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Static files and templates
    static_path = Path(__file__).parent / "static"
    templates_path = Path(__file__).parent / "templates"
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    templates = Jinja2Templates(directory=str(templates_path))

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        """Liveness probe used by deployment platforms and monitoring."""
        return {"status": "ok", "app": settings.app_name}

    @app.get("/", response_class=HTMLResponse, tags=["frontend"])
    async def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request=request, name="login.html")

    @app.get("/login", response_class=HTMLResponse, tags=["frontend"])
    async def login_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request=request, name="login.html")

    @app.get("/register", response_class=HTMLResponse, tags=["frontend"])
    async def register_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request=request, name="register.html")

    @app.get("/dashboard/teacher", response_class=HTMLResponse, tags=["frontend"])
    async def teacher_dashboard(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request=request, name="teacher_dashboard.html", context={"nav_mode": "auth"})

    @app.get("/dashboard/student", response_class=HTMLResponse, tags=["frontend"])
    async def student_dashboard(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request=request, name="student_dashboard.html", context={"nav_mode": "auth"})

    @app.get("/api/v1/me", tags=["auth"])
    async def read_current_user(user: User = Depends(get_current_user)) -> dict:
        """Temporary test route — confirms JWT auth is wired correctly."""
        return {"id": user.id, "email": user.email, "role": user.role}

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(exams_router, prefix="/api/v1")
    app.include_router(submissions_router, prefix="/api/v1")
    app.include_router(reports_router, prefix="/api/v1")

    return app


app = create_app()