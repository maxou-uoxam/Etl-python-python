"""Database initialization."""
from loguru import logger
from etl_app.database.base import Base, engine


def init_db() -> None:
    """Create all tables if they don't exist."""
    # Import models to register them with Base metadata
    from etl_app.core.models import (  # noqa: F401
        Project, ProjectEnvironment,
        PipelineStep,
        DatabaseConnection,
        ExecutionRecord, ExecutionLog,
    )
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
