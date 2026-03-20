from .projects import router as projects_router
from .pipeline import router as pipeline_router
from .connections import router as connections_router
from .execution import router as execution_router
from .documentation import router as documentation_router
from .ui import router as ui_router

__all__ = [
    "projects_router",
    "pipeline_router",
    "connections_router",
    "execution_router",
    "documentation_router",
    "ui_router",
]
