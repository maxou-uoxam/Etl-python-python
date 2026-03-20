"""Pipeline ViewModel."""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from etl_app.core.services.project_service import ProjectService
from etl_app.core.services.csv_service import CsvService
from etl_app.core.models.pipeline import StepType


class PipelineViewModel:
    def __init__(self, db: Session):
        self.project_svc = ProjectService(db)
        self.csv_svc = CsvService()

    def get_ingestion_data(self, project_id: int) -> Dict[str, Any]:
        config = self.project_svc.get_step_config(project_id, StepType.INGESTION)
        return {
            "project_id": project_id,
            "step_type": StepType.INGESTION.value,
            "config": config or {},
            "encodings": ["utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"],
            "delimiters": [
                {"value": ";", "label": "Point-virgule (;)"},
                {"value": ",", "label": "Virgule (,)"},
                {"value": "\t", "label": "Tabulation (\\t)"},
                {"value": "|", "label": "Pipe (|)"},
            ],
        }

    def get_staging_data(self, project_id: int) -> Dict[str, Any]:
        config = self.project_svc.get_step_config(project_id, StepType.STAGING)
        ingestion_cfg = self.project_svc.get_step_config(project_id, StepType.INGESTION)

        columns = []
        if ingestion_cfg and ingestion_cfg.get("file_path"):
            preview = self.csv_svc.get_preview(
                ingestion_cfg["file_path"],
                delimiter=ingestion_cfg.get("delimiter", ";"),
                encoding=ingestion_cfg.get("encoding", "utf-8-sig"),
                page_size=1,
            )
            columns = preview.get("columns", [])

        return {
            "project_id": project_id,
            "step_type": StepType.STAGING.value,
            "config": config or {},
            "available_columns": columns,
        }

    def get_ods_data(self, project_id: int) -> Dict[str, Any]:
        config = self.project_svc.get_step_config(project_id, StepType.ODS)
        staging_cfg = self.project_svc.get_step_config(project_id, StepType.STAGING)
        columns = staging_cfg.get("selected_columns", []) if staging_cfg else []

        return {
            "project_id": project_id,
            "step_type": StepType.ODS.value,
            "config": config or {},
            "source_columns": columns,
            "sql_types": ["NVARCHAR", "INT", "BIGINT", "DECIMAL", "DATE",
                          "DATETIME2", "BIT", "FLOAT"],
        }

    def get_dimension_data(self, project_id: int) -> Dict[str, Any]:
        config = self.project_svc.get_step_config(project_id, StepType.DIMENSION)
        ods_cfg = self.project_svc.get_step_config(project_id, StepType.ODS)
        columns = ods_cfg.get("selected_columns", []) if ods_cfg else []
        if ods_cfg:
            mappings = ods_cfg.get("column_mappings", [])
            if mappings:
                columns = [m.get("target_column", m.get("source_column"))
                           for m in mappings]

        return {
            "project_id": project_id,
            "step_type": StepType.DIMENSION.value,
            "config": config or {},
            "ods_columns": columns,
        }

    def get_fact_data(self, project_id: int) -> Dict[str, Any]:
        config = self.project_svc.get_step_config(project_id, StepType.FACT)
        ods_cfg = self.project_svc.get_step_config(project_id, StepType.ODS)
        columns = []
        if ods_cfg:
            mappings = ods_cfg.get("column_mappings", [])
            if mappings:
                columns = [m.get("target_column", m.get("source_column"))
                           for m in mappings]
            else:
                columns = ods_cfg.get("selected_columns", [])

        return {
            "project_id": project_id,
            "step_type": StepType.FACT.value,
            "config": config or {},
            "ods_columns": columns,
        }
