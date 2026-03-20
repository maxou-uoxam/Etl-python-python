"""Execution control and monitoring API routes."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from etl_app.database import get_db
from etl_app.core.models.project import EnvironmentType
from etl_app.core.repositories import ExecutionRepository
from etl_app.etl.executor import EtlExecutor

router = APIRouter(prefix="/api/executions", tags=["Executions"])


class RunRequest(BaseModel):
    environment: EnvironmentType
    is_dry_run: bool = False


@router.post("/projects/{project_id}/run", status_code=202)
def run_pipeline(
    project_id: int,
    data: RunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger pipeline execution (async via background task)."""
    executor = EtlExecutor(db)
    try:
        exec_id = executor.run(project_id, data.environment, data.is_dry_run)
        return {
            "execution_id": exec_id,
            "message": "Pipeline started",
            "dry_run": data.is_dry_run,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}")
def list_executions(project_id: int, db: Session = Depends(get_db)):
    repo = ExecutionRepository(db)
    records = repo.get_for_project(project_id)
    return [
        {
            "id": r.id,
            "environment": r.environment,
            "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "duration_seconds": r.duration_seconds,
            "rows_processed": r.rows_processed,
            "is_dry_run": r.is_dry_run,
        }
        for r in records
    ]


@router.get("/{execution_id}")
def get_execution(execution_id: int, db: Session = Depends(get_db)):
    repo = ExecutionRepository(db)
    record = repo.get_with_logs(execution_id)
    if not record:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {
        "id": record.id,
        "project_id": record.project_id,
        "environment": record.environment,
        "status": record.status,
        "started_at": record.started_at.isoformat() if record.started_at else None,
        "finished_at": record.finished_at.isoformat() if record.finished_at else None,
        "duration_seconds": record.duration_seconds,
        "rows_processed": record.rows_processed,
        "is_dry_run": record.is_dry_run,
        "error_message": record.error_message,
        "step_results": record.step_results,
        "logs": [
            {
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "level": log.level,
                "step_type": log.step_type,
                "message": log.message,
            }
            for log in record.logs
        ],
    }


@router.get("/running")
def get_running_executions(db: Session = Depends(get_db)):
    repo = ExecutionRepository(db)
    records = repo.get_running()
    return [{"id": r.id, "project_id": r.project_id,
             "environment": r.environment} for r in records]
