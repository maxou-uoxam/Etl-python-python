"""Project ViewModel — bridges service layer and API/UI."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from etl_app.core.services.project_service import ProjectService
from etl_app.core.services.connection_service import ConnectionService
from etl_app.core.models.project import EnvironmentType
from etl_app.core.models.pipeline import StepType


class ProjectViewModel:
    def __init__(self, db: Session):
        self.project_svc = ProjectService(db)
        self.conn_svc = ConnectionService(db)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Data for the main dashboard view."""
        projects = self.project_svc.list_projects()
        connections = self.conn_svc.list_connections()
        return {
            "projects": [self._project_summary(p) for p in projects],
            "total_projects": len(projects),
            "total_connections": len(connections),
            "environments": [e.value for e in EnvironmentType],
        }

    def get_project_detail(self, project_id: int) -> Optional[Dict[str, Any]]:
        project = self.project_svc.get_project(project_id)
        if not project:
            return None

        steps = {}
        for step in (project.steps or []):
            steps[step.step_type] = {
                "id": step.id,
                "name": step.name,
                "order": step.order,
                "status": step.status,
                "config": step.config or {},
            }

        environments = {}
        for env in (project.environments or []):
            environments[env.env_type.value] = {
                "id": env.id,
                "source_base_path": env.source_base_path,
                "source_product": env.source_product,
                "connection_id": env.connection_id,
                "staging_schema": env.staging_schema,
                "ods_schema": env.ods_schema,
                "dim_schema": env.dim_schema,
                "fact_schema": env.fact_schema,
                "input_path": env.get_input_path(),
                "output_path": env.get_output_path(),
            }

        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "version": project.version,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "steps": steps,
            "environments": environments,
            "step_types": [s.value for s in StepType],
            "environment_types": [e.value for e in EnvironmentType],
            "connections": [
                {"id": c.id, "name": c.name, "server": c.server}
                for c in self.conn_svc.list_connections()
            ],
        }

    def _project_summary(self, project) -> Dict[str, Any]:
        step_count = len(project.steps) if project.steps else 0
        configured = sum(
            1 for s in (project.steps or []) if s.status == "configured"
        )
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description or "",
            "version": project.version,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "step_count": step_count,
            "configured_steps": configured,
            "progress": round((configured / 6) * 100) if step_count > 0 else 0,
        }
