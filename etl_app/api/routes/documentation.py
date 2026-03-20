"""Documentation generation API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from etl_app.database import get_db
from etl_app.core.viewmodels.documentation_vm import DocumentationViewModel

router = APIRouter(prefix="/api/documentation", tags=["Documentation"])


@router.post("/{project_id}/generate")
def generate_documentation(project_id: int, db: Session = Depends(get_db)):
    vm = DocumentationViewModel(db)
    result = vm.generate_and_save(project_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/{project_id}/lineage")
def get_lineage(project_id: int, db: Session = Depends(get_db)):
    vm = DocumentationViewModel(db)
    result = vm.generate_and_save(project_id)
    return {"lineage": result.get("lineage_preview", ""), "mermaid": result.get("mermaid", "")}


@router.get("/{project_id}/metrics")
def get_metrics(project_id: int, db: Session = Depends(get_db)):
    vm = DocumentationViewModel(db)
    result = vm.generate_and_save(project_id)
    return {"metrics": result.get("metrics", "{}")}
