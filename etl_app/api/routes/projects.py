"""Project CRUD API routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from etl_app.database import get_db
from etl_app.core.services.project_service import ProjectService
from etl_app.core.viewmodels.project_vm import ProjectViewModel
from etl_app.core.models.project import EnvironmentType

router = APIRouter(prefix="/api/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class EnvironmentUpdate(BaseModel):
    source_base_path: Optional[str] = None
    source_product: Optional[str] = None
    connection_id: Optional[int] = None
    staging_schema: str = "sta"
    ods_schema: str = "ods"
    dim_schema: str = "dim"
    fact_schema: str = "fait"


@router.get("/")
def list_projects(
    q: Optional[str] = Query(None, description="Search query"),
    db: Session = Depends(get_db),
):
    svc = ProjectService(db)
    if q:
        projects = svc.search_projects(q)
    else:
        projects = svc.list_projects()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "version": p.version,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in projects
    ]


@router.post("/", status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    try:
        project = svc.create_project(data.name, data.description)
        return {"id": project.id, "name": project.name, "message": "Project created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    vm = ProjectViewModel(db)
    data = vm.get_project_detail(project_id)
    if not data:
        raise HTTPException(status_code=404, detail="Project not found")
    return data


@router.put("/{project_id}")
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    try:
        project = svc.update_project(project_id, data.name, data.description)
        return {"id": project.id, "name": project.name, "message": "Project updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    try:
        svc.delete_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{project_id}/environments/{env_type}")
def save_environment(
    project_id: int,
    env_type: EnvironmentType,
    data: EnvironmentUpdate,
    db: Session = Depends(get_db),
):
    svc = ProjectService(db)
    try:
        env = svc.save_environment(project_id, env_type, data.dict())
        return {"id": env.id, "env_type": env.env_type.value, "message": "Environment saved"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/export")
def export_project(project_id: int, db: Session = Depends(get_db)):
    from fastapi.responses import Response
    svc = ProjectService(db)
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from etl_app.core.services.yaml_service import YamlService
    yaml_svc = YamlService()
    zip_bytes = yaml_svc.export_project(project.name)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={project.name}.zip"},
    )
