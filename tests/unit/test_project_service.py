"""Unit tests for ProjectService."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from etl_app.database.base import Base
from etl_app.core.models import Project, ProjectEnvironment, PipelineStep, DatabaseConnection, ExecutionRecord, ExecutionLog
from etl_app.core.services.project_service import ProjectService
from etl_app.core.models.pipeline import StepType


@pytest.fixture
def db():
    """In-memory SQLite for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestProjectService:
    def test_create_project(self, db):
        svc = ProjectService(db)
        project = svc.create_project("TEST_PROJ", "Test project")
        assert project.id is not None
        assert project.name == "TEST_PROJ"
        assert len(project.steps) == 6  # 6 default steps

    def test_create_duplicate_raises(self, db):
        svc = ProjectService(db)
        svc.create_project("DUPLICATE")
        with pytest.raises(ValueError, match="already exists"):
            svc.create_project("DUPLICATE")

    def test_update_project(self, db):
        svc = ProjectService(db)
        project = svc.create_project("PROJ1")
        updated = svc.update_project(project.id, description="Updated desc")
        assert updated.description == "Updated desc"

    def test_delete_project(self, db):
        svc = ProjectService(db)
        project = svc.create_project("TO_DELETE")
        result = svc.delete_project(project.id)
        assert result is True
        assert svc.get_project(project.id) is None

    def test_save_step_config(self, db):
        svc = ProjectService(db)
        project = svc.create_project("STEP_TEST")
        config = {"file_path": "/data/test.csv", "delimiter": ";"}
        step = svc.save_step_config(project.id, StepType.INGESTION, config)
        assert step.config["file_path"] == "/data/test.csv"

    def test_get_step_config(self, db):
        svc = ProjectService(db)
        project = svc.create_project("CONFIG_TEST")
        config = {"table_name": "sta_test", "batch_size": 500}
        svc.save_step_config(project.id, StepType.STAGING, config)
        retrieved = svc.get_step_config(project.id, StepType.STAGING)
        assert retrieved["table_name"] == "sta_test"

    def test_list_projects(self, db):
        svc = ProjectService(db)
        svc.create_project("PROJ_A")
        svc.create_project("PROJ_B")
        projects = svc.list_projects()
        assert len(projects) >= 2

    def test_search_projects(self, db):
        svc = ProjectService(db)
        svc.create_project("VENTES_2024")
        svc.create_project("ACHATS_2024")
        results = svc.search_projects("VENTES")
        assert len(results) == 1
        assert results[0].name == "VENTES_2024"
