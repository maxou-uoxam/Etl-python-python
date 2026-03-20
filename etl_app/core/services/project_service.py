"""Project management service."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from etl_app.core.models.project import Project, ProjectEnvironment, EnvironmentType
from etl_app.core.models.pipeline import (
    PipelineStep, StepType, StepStatus,
    StagingConfig, OdsConfig, DimensionConfig, FactConfig
)
from etl_app.core.repositories import ProjectRepository
from etl_app.core.services.yaml_service import YamlService


STEP_ORDER = {
    StepType.INGESTION: 1,
    StepType.STAGING: 2,
    StepType.ODS: 3,
    StepType.DIMENSION: 4,
    StepType.FACT: 5,
    StepType.POST_PROCESSING: 6,
}


class ProjectService:
    def __init__(self, db: Session):
        self.repo = ProjectRepository(db)
        self.yaml_svc = YamlService()

    # ── Project CRUD ──────────────────────────────────────────────────────────

    def create_project(self, name: str, description: str = "") -> Project:
        if self.repo.get_by_name(name):
            raise ValueError(f"Project '{name}' already exists.")

        project = Project(name=name, description=description)
        project = self.repo.create(project)
        self._initialize_default_steps(project)

        # Save YAML skeleton
        self._save_yaml(project)
        logger.info(f"Project '{name}' created (id={project.id})")
        return project

    def update_project(self, project_id: int, name: str = None,
                        description: str = None) -> Project:
        project = self.repo.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found.")
        if name and name != project.name:
            if self.repo.get_by_name(name):
                raise ValueError(f"Project '{name}' already exists.")
            project.name = name
        if description is not None:
            project.description = description
        project.updated_at = datetime.utcnow()
        project = self.repo.update(project)
        self._save_yaml(project)
        return project

    def delete_project(self, project_id: int) -> bool:
        project = self.repo.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found.")
        result = self.repo.delete(project_id)
        logger.info(f"Project {project_id} deleted.")
        return result

    def get_project(self, project_id: int) -> Optional[Project]:
        return self.repo.get_with_details(project_id)

    def list_projects(self) -> List[Project]:
        return self.repo.get_active_projects()

    def search_projects(self, query: str) -> List[Project]:
        return self.repo.search(query)

    # ── Step config ───────────────────────────────────────────────────────────

    def save_step_config(self, project_id: int, step_type: StepType,
                          config: dict) -> PipelineStep:
        project = self.repo.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found.")

        step = self.repo.upsert_step(
            project_id=project_id,
            step_type=step_type.value,
            name=step_type.value.replace("_", " ").title(),
            order=STEP_ORDER[step_type],
            config=config,
        )
        self._save_yaml(project)
        return step

    def get_step_config(self, project_id: int, step_type: StepType) -> Optional[dict]:
        step = self.repo.get_step(project_id, step_type.value)
        return step.config if step else {}

    # ── Environment ───────────────────────────────────────────────────────────

    def save_environment(self, project_id: int, env_type: EnvironmentType,
                          env_data: dict) -> ProjectEnvironment:
        project = self.repo.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found.")

        env = ProjectEnvironment(
            project_id=project_id,
            env_type=env_type,
            **{k: v for k, v in env_data.items()
               if k in ["source_base_path", "source_product", "connection_id",
                        "staging_schema", "ods_schema", "dim_schema", "fact_schema"]}
        )
        return self.repo.upsert_environment(env)

    # ── YAML Serialization ────────────────────────────────────────────────────

    def _save_yaml(self, project: Project) -> None:
        project = self.repo.get_with_details(project.id)
        config = self._to_yaml_dict(project)
        path = self.yaml_svc.save_project(project.name, config)
        # Store path reference
        if project.yaml_path != str(path):
            project.yaml_path = str(path)
            self.repo.update(project)

    def _to_yaml_dict(self, project: Project) -> Dict[str, Any]:
        envs = {}
        for env in (project.environments or []):
            envs[env.env_type.value] = {
                "source_base_path": env.source_base_path,
                "source_product": env.source_product,
                "connection_id": env.connection_id,
                "staging_schema": env.staging_schema,
                "ods_schema": env.ods_schema,
                "dim_schema": env.dim_schema,
                "fact_schema": env.fact_schema,
            }

        steps = {}
        for step in (project.steps or []):
            steps[step.step_type] = {
                "name": step.name,
                "order": step.order,
                "status": step.status,
                "config": step.config or {},
            }

        return {
            "name": project.name,
            "description": project.description,
            "version": project.version,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "environments": envs,
            "pipeline": {
                "steps": steps,
            },
        }

    def _initialize_default_steps(self, project: Project) -> None:
        default_steps = [
            (StepType.INGESTION, "Ingestion CSV"),
            (StepType.STAGING, "Chargement Staging"),
            (StepType.ODS, "Transformation ODS"),
            (StepType.DIMENSION, "Création Dimensions"),
            (StepType.FACT, "Table de Faits"),
            (StepType.POST_PROCESSING, "Post-traitement"),
        ]
        for step_type, name in default_steps:
            self.repo.upsert_step(
                project_id=project.id,
                step_type=step_type.value,
                name=name,
                order=STEP_ORDER[step_type],
                config={},
            )

    def get_project_stats(self) -> Dict[str, Any]:
        projects = self.list_projects()
        return {
            "total_projects": len(projects),
            "active_projects": sum(1 for p in projects if p.is_active),
            "projects": [
                {"id": p.id, "name": p.name, "updated_at": p.updated_at.isoformat()}
                for p in projects
            ],
        }
