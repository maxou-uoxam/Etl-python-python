"""Pipeline step configuration API routes."""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from etl_app.database import get_db
from etl_app.core.services.project_service import ProjectService
from etl_app.core.services.csv_service import CsvService
from etl_app.core.models.pipeline import StepType
from etl_app.core.viewmodels.pipeline_vm import PipelineViewModel

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])


class StepConfig(BaseModel):
    config: Dict[str, Any]


@router.get("/{project_id}/steps/{step_type}")
def get_step(project_id: int, step_type: StepType,
             db: Session = Depends(get_db)):
    svc = ProjectService(db)
    config = svc.get_step_config(project_id, step_type)
    return {"project_id": project_id, "step_type": step_type.value, "config": config}


@router.put("/{project_id}/steps/{step_type}")
def save_step(project_id: int, step_type: StepType,
              data: StepConfig, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    try:
        step = svc.save_step_config(project_id, step_type, data.config)
        return {
            "id": step.id,
            "step_type": step.step_type,
            "status": step.status,
            "message": "Step configuration saved",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{project_id}/csv/detect")
def detect_csv_format(project_id: int, file_path: str,
                       db: Session = Depends(get_db)):
    svc = CsvService()
    result = svc.detect_format(file_path)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{project_id}/csv/preview")
def preview_csv(
    project_id: int,
    file_path: str,
    delimiter: str = ";",
    encoding: str = "utf-8-sig",
    has_header: bool = True,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    svc = CsvService()
    result = svc.get_preview(file_path, delimiter, encoding, has_header, page, page_size)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{project_id}/csv/column-types")
def detect_column_types(
    project_id: int,
    file_path: str,
    delimiter: str = ";",
    encoding: str = "utf-8-sig",
    db: Session = Depends(get_db),
):
    svc = CsvService()
    return svc.detect_column_types(file_path, delimiter, encoding)


@router.get("/{project_id}/csv/files")
def list_csv_files(project_id: int, folder: str,
                    db: Session = Depends(get_db)):
    svc = CsvService()
    return svc.list_csv_files(folder)


@router.get("/{project_id}/view/ingestion")
def ingestion_view_data(project_id: int, db: Session = Depends(get_db)):
    vm = PipelineViewModel(db)
    return vm.get_ingestion_data(project_id)


@router.get("/{project_id}/view/staging")
def staging_view_data(project_id: int, db: Session = Depends(get_db)):
    vm = PipelineViewModel(db)
    return vm.get_staging_data(project_id)


@router.get("/{project_id}/view/ods")
def ods_view_data(project_id: int, db: Session = Depends(get_db)):
    vm = PipelineViewModel(db)
    return vm.get_ods_data(project_id)


@router.get("/{project_id}/view/dimension")
def dimension_view_data(project_id: int, db: Session = Depends(get_db)):
    vm = PipelineViewModel(db)
    return vm.get_dimension_data(project_id)


@router.get("/{project_id}/view/fact")
def fact_view_data(project_id: int, db: Session = Depends(get_db)):
    vm = PipelineViewModel(db)
    return vm.get_fact_data(project_id)
