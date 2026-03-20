"""Documentation ViewModel."""
from typing import Dict, Any
from sqlalchemy.orm import Session

from etl_app.core.services.project_service import ProjectService
from etl_app.core.services.yaml_service import YamlService
from etl_app.etl.generators import DocumentationGenerator, SqlGenerator


class DocumentationViewModel:
    def __init__(self, db: Session):
        self.project_svc = ProjectService(db)
        self.yaml_svc = YamlService()
        self.doc_gen = DocumentationGenerator()
        self.sql_gen = SqlGenerator()

    def generate_and_save(self, project_id: int) -> Dict[str, Any]:
        """Generate all documentation and SQL files, save to disk."""
        project = self.project_svc.get_project(project_id)
        if not project:
            return {"error": "Project not found"}

        project_config = self.project_svc._to_yaml_dict(project)

        # Documentation
        lineage_md = self.doc_gen.generate_data_lineage(project, project_config)
        metrics_json = self.doc_gen.generate_metrics(project, project_config)
        mermaid = self.doc_gen.generate_mermaid_diagram(project, project_config)

        self.yaml_svc.save_documentation(project.name, "data_lineage.md", lineage_md)
        self.yaml_svc.save_documentation(project.name, "metrics.json", metrics_json)
        self.yaml_svc.save_documentation(project.name, "schema_diagram.mmd", mermaid)

        # SQL scripts
        sql_files = self.sql_gen.generate_all(project_config)
        for path, content in sql_files.items():
            parts = path.split("/", 1)
            if len(parts) == 2:
                self.yaml_svc.save_sql(project.name, parts[1], content)

        return {
            "success": True,
            "project": project.name,
            "files_generated": len(sql_files) + 3,
            "lineage_preview": lineage_md[:500],
            "mermaid": mermaid,
            "metrics": metrics_json,
        }
