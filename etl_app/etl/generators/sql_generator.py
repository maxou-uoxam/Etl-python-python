"""SQL code generator for all pipeline steps."""
from typing import Dict, Any
from etl_app.core.models.pipeline import StepType
from etl_app.etl.steps.staging import StagingStep
from etl_app.etl.steps.ods import OdsStep
from etl_app.etl.steps.dimension import DimensionStep
from etl_app.etl.steps.fact import FactStep


class SqlGenerator:
    """Generate SQL scripts from step configurations."""

    def generate_all(self, project_config: Dict[str, Any]) -> Dict[str, str]:
        """Generate all SQL files for a project."""
        steps = project_config.get("pipeline", {}).get("steps", {})
        results = {}

        staging_cfg = steps.get(StepType.STAGING.value, {}).get("config", {})
        ods_cfg = steps.get(StepType.ODS.value, {}).get("config", {})
        dim_cfg = steps.get(StepType.DIMENSION.value, {}).get("config", {})
        fact_cfg = steps.get(StepType.FACT.value, {}).get("config", {})

        # Use dummy conn_str — generation only
        dummy = ""

        if staging_cfg.get("table_name"):
            step = StagingStep(conn_str=dummy)
            results["transformations/staging/load_staging.sql"] = step.generate_sql(staging_cfg)

        if ods_cfg.get("table_name"):
            step = OdsStep(conn_str=dummy)
            results["transformations/ods/transformations.sql"] = step.generate_sql(ods_cfg)

        if dim_cfg.get("table_name"):
            step = DimensionStep(conn_str=dummy)
            table = dim_cfg["table_name"]
            results[f"transformations/dwh/dimensions/dim_{table}.sql"] = step.generate_sql(dim_cfg)

        if fact_cfg.get("table_name"):
            step = FactStep(conn_str=dummy)
            table = fact_cfg["table_name"]
            results[f"transformations/dwh/facts/fact_{table}.sql"] = step.generate_sql(fact_cfg)

        return results
