"""Project repository with project-specific queries."""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from etl_app.core.models.project import Project, ProjectEnvironment, EnvironmentType
from etl_app.core.models.pipeline import PipelineStep
from .base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: Session):
        super().__init__(Project, db)

    def get_by_name(self, name: str) -> Optional[Project]:
        return self.db.query(Project).filter(Project.name == name).first()

    def get_with_details(self, id: int) -> Optional[Project]:
        return (
            self.db.query(Project)
            .options(
                joinedload(Project.environments).joinedload(ProjectEnvironment.connection),
                joinedload(Project.steps),
            )
            .filter(Project.id == id)
            .first()
        )

    def get_active_projects(self) -> List[Project]:
        return (
            self.db.query(Project)
            .filter(Project.is_active == True)
            .order_by(Project.updated_at.desc())
            .all()
        )

    def search(self, query: str) -> List[Project]:
        return (
            self.db.query(Project)
            .filter(Project.name.ilike(f"%{query}%"))
            .all()
        )

    def get_step(self, project_id: int, step_type: str) -> Optional[PipelineStep]:
        return (
            self.db.query(PipelineStep)
            .filter(
                PipelineStep.project_id == project_id,
                PipelineStep.step_type == step_type,
            )
            .first()
        )

    def upsert_step(self, project_id: int, step_type: str,
                    name: str, order: int, config: dict) -> PipelineStep:
        step = self.get_step(project_id, step_type)
        if step:
            step.config = config
            step.name = name
            from etl_app.core.models.pipeline import StepStatus
            step.status = StepStatus.CONFIGURED
        else:
            from etl_app.core.models.pipeline import StepStatus
            step = PipelineStep(
                project_id=project_id,
                step_type=step_type,
                order=order,
                name=name,
                config=config,
                status=StepStatus.CONFIGURED,
            )
            self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def get_environment(self, project_id: int,
                         env_type: EnvironmentType) -> Optional[ProjectEnvironment]:
        return (
            self.db.query(ProjectEnvironment)
            .filter(
                ProjectEnvironment.project_id == project_id,
                ProjectEnvironment.env_type == env_type,
            )
            .first()
        )

    def upsert_environment(self, env: ProjectEnvironment) -> ProjectEnvironment:
        existing = self.get_environment(env.project_id, env.env_type)
        if existing:
            for attr in ["source_base_path", "source_product", "connection_id",
                         "staging_schema", "ods_schema", "dim_schema", "fact_schema"]:
                val = getattr(env, attr, None)
                if val is not None:
                    setattr(existing, attr, val)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        self.db.add(env)
        self.db.commit()
        self.db.refresh(env)
        return env
