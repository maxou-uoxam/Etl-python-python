"""FastAPI application factory."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from etl_app.config import settings
from etl_app.database import init_db
from etl_app.api.routes import (
    projects_router,
    pipeline_router,
    connections_router,
    execution_router,
    documentation_router,
    ui_router,
)

STATIC_DIR = Path(__file__).parent.parent / "ui" / "static"
TEMPLATES_DIR = Path(__file__).parent.parent / "ui" / "templates"


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="ETL Manager — Modern Python ETL Pipeline Builder",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # CORS for local dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static files
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Templates
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.state.templates = templates

    # Register routers
    app.include_router(ui_router)
    app.include_router(projects_router)
    app.include_router(pipeline_router)
    app.include_router(connections_router)
    app.include_router(execution_router)
    app.include_router(documentation_router)

    @app.on_event("startup")
    async def startup():
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        settings.projects_dir.mkdir(parents=True, exist_ok=True)
        init_db()
        logger.info(f"Server running at http://{settings.host}:{settings.port}")

    return app
