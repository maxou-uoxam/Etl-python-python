"""Integration tests for the FastAPI application."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from etl_app.database.base import Base, get_db
from etl_app.api.app import create_app


@pytest.fixture(scope="module")
def client():
    """Test client with in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    from etl_app.core.models import (  # noqa
        Project, ProjectEnvironment, PipelineStep, DatabaseConnection,
        ExecutionRecord, ExecutionLog,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    return TestClient(app)


class TestProjectAPI:
    def test_list_projects_empty(self, client):
        res = client.get("/api/projects/")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_create_project(self, client):
        res = client.post("/api/projects/", json={"name": "TEST_API", "description": "Test"})
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "TEST_API"
        assert "id" in data

    def test_create_duplicate_project(self, client):
        client.post("/api/projects/", json={"name": "DUPE_TEST"})
        res = client.post("/api/projects/", json={"name": "DUPE_TEST"})
        assert res.status_code == 400

    def test_get_project(self, client):
        res = client.post("/api/projects/", json={"name": "GET_TEST"})
        project_id = res.json()["id"]
        res2 = client.get(f"/api/projects/{project_id}")
        assert res2.status_code == 200
        assert res2.json()["name"] == "GET_TEST"

    def test_get_nonexistent_project(self, client):
        res = client.get("/api/projects/99999")
        assert res.status_code == 404

    def test_delete_project(self, client):
        res = client.post("/api/projects/", json={"name": "TO_DELETE_API"})
        project_id = res.json()["id"]
        del_res = client.delete(f"/api/projects/{project_id}")
        assert del_res.status_code == 204

    def test_update_step_config(self, client):
        res = client.post("/api/projects/", json={"name": "STEP_CONFIG_TEST"})
        project_id = res.json()["id"]
        config_res = client.put(
            f"/api/pipeline/{project_id}/steps/ingestion",
            json={"config": {"file_path": "/test/file.csv", "delimiter": ";"}}
        )
        assert config_res.status_code == 200


class TestConnectionAPI:
    def test_list_connections_empty(self, client):
        res = client.get("/api/connections/")
        assert res.status_code == 200

    def test_create_connection(self, client):
        res = client.post("/api/connections/", json={
            "name": "TEST_CONN",
            "server": "localhost",
            "database": "TestDB",
            "use_windows_auth": True,
        })
        assert res.status_code == 201
        assert res.json()["name"] == "TEST_CONN"
