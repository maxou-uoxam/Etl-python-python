"""HTML UI routes (server-rendered with Jinja2)."""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from etl_app.database import get_db
from etl_app.core.viewmodels.project_vm import ProjectViewModel
from etl_app.core.viewmodels.pipeline_vm import PipelineViewModel
from etl_app.core.models.pipeline import StepType
from etl_app.core.services.connection_service import ConnectionService

router = APIRouter(tags=["UI"])


def get_templates(request: Request):
    return request.app.state.templates


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    vm = ProjectViewModel(db)
    data = vm.get_dashboard_data()
    templates = get_templates(request)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, **data},
    )


@router.get("/projects/new", response_class=HTMLResponse)
def new_project_form(request: Request, db: Session = Depends(get_db)):
    templates = get_templates(request)
    return templates.TemplateResponse(
        "project_form.html",
        {"request": request, "project": None, "mode": "create"},
    )


@router.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(project_id: int, request: Request,
                    db: Session = Depends(get_db)):
    vm = ProjectViewModel(db)
    data = vm.get_project_detail(project_id)
    if not data:
        raise HTTPException(status_code=404, detail="Project not found")
    templates = get_templates(request)
    return templates.TemplateResponse(
        "project_detail.html",
        {"request": request, **data},
    )


@router.get("/projects/{project_id}/pipeline/{step_type}", response_class=HTMLResponse)
def pipeline_step(
    project_id: int,
    step_type: str,
    request: Request,
    db: Session = Depends(get_db),
):
    vm = PipelineViewModel(db)
    templates = get_templates(request)

    step_data_map = {
        "ingestion": vm.get_ingestion_data,
        "staging": vm.get_staging_data,
        "ods": vm.get_ods_data,
        "dimension": vm.get_dimension_data,
        "fact": vm.get_fact_data,
    }

    get_data = step_data_map.get(step_type)
    if not get_data:
        raise HTTPException(status_code=404, detail=f"Unknown step: {step_type}")

    data = get_data(project_id)
    return templates.TemplateResponse(
        f"steps/{step_type}.html",
        {"request": request, **data},
    )


@router.get("/connections", response_class=HTMLResponse)
def connections_page(request: Request, db: Session = Depends(get_db)):
    svc = ConnectionService(db)
    connections = svc.list_connections()
    templates = get_templates(request)
    return templates.TemplateResponse(
        "connections.html",
        {
            "request": request,
            "connections": [
                {
                    "id": c.id,
                    "name": c.name,
                    "server": c.server,
                    "database": c.database,
                    "use_windows_auth": c.use_windows_auth,
                }
                for c in connections
            ],
        },
    )


@router.get("/projects/{project_id}/documentation", response_class=HTMLResponse)
def documentation_page(project_id: int, request: Request,
                         db: Session = Depends(get_db)):
    from etl_app.core.viewmodels.documentation_vm import DocumentationViewModel
    vm = DocumentationViewModel(db)
    data = vm.generate_and_save(project_id)
    templates = get_templates(request)
    return templates.TemplateResponse(
        "documentation.html",
        {"request": request, "project_id": project_id, **data},
    )
