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
    _fix_empty_configured_steps()


def _fix_empty_configured_steps() -> None:
    """Reset steps with empty config that were incorrectly marked as CONFIGURED."""
    from etl_app.database.base import SessionLocal
    from etl_app.core.models.pipeline import PipelineStep, StepStatus

    db = SessionLocal()
    try:
        steps = (
            db.query(PipelineStep)
            .filter(PipelineStep.status == StepStatus.CONFIGURED)
            .all()
        )
        fixed = 0
        for step in steps:
            config = step.config or {}
            # A step is genuinely configured only if its config contains meaningful data
            has_data = any(v for v in config.values() if v not in (None, "", [], {}))
            if not has_data:
                step.status = StepStatus.PENDING
                fixed += 1
        if fixed:
            db.commit()
            logger.info(f"Fixed {fixed} steps incorrectly marked as CONFIGURED → reset to PENDING.")
    except Exception as e:
        logger.error(f"Error fixing step statuses: {e}")
        db.rollback()
    finally:
        db.close()
