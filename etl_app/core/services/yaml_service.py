"""YAML serialization service for Git-friendly project configs."""
import json
from pathlib import Path
from typing import Any, Dict
import yaml
from loguru import logger
from etl_app.config import settings


class YamlService:
    def __init__(self):
        self.projects_dir = settings.projects_dir
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def save_project(self, project_name: str, config: Dict[str, Any]) -> Path:
        """Save project configuration to YAML."""
        project_dir = self.projects_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        yaml_path = project_dir / "project.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False,
                      allow_unicode=True, sort_keys=False, indent=2)

        logger.info(f"Project saved to {yaml_path}")
        return yaml_path

    def load_project(self, project_name: str) -> Dict[str, Any]:
        """Load project configuration from YAML."""
        yaml_path = self.projects_dir / project_name / "project.yaml"
        if not yaml_path.exists():
            return {}
        with open(yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def save_schema(self, project_name: str, schema_type: str,
                    schema: Dict[str, Any]) -> Path:
        """Save schema definition (staging/ods/dwh tables)."""
        schema_dir = self.projects_dir / project_name / "schemas"
        schema_dir.mkdir(parents=True, exist_ok=True)
        path = schema_dir / f"{schema_type}_tables.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        return path

    def save_sql(self, project_name: str, sub_path: str, sql: str) -> Path:
        """Save generated SQL file."""
        full_path = self.projects_dir / project_name / "transformations" / sub_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(sql)
        return full_path

    def save_documentation(self, project_name: str,
                            doc_type: str, content: str) -> Path:
        """Save documentation file (markdown/json/mermaid)."""
        doc_dir = self.projects_dir / project_name / "documentation"
        doc_dir.mkdir(parents=True, exist_ok=True)
        path = doc_dir / doc_type
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def export_project(self, project_name: str) -> bytes:
        """Export entire project directory as YAML bundle."""
        import zipfile
        import io
        project_dir = self.projects_dir / project_name
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in project_dir.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(self.projects_dir))
        return buf.getvalue()
