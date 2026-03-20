"""Main ETL pipeline executor."""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from etl_app.core.models.project import EnvironmentType
from etl_app.core.models.execution import ExecutionStatus
from etl_app.core.models.pipeline import StepType
from etl_app.core.repositories import ProjectRepository, ExecutionRepository
from etl_app.core.services.connection_service import ConnectionService
from etl_app.etl.steps import (
    IngestionStep, StagingStep, OdsStep,
    DimensionStep, FactStep, PostProcessingStep,
)


class EtlExecutor:
    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.exec_repo = ExecutionRepository(db)
        self.conn_svc = ConnectionService(db)

    def run(self, project_id: int, env_type: EnvironmentType,
            is_dry_run: bool = False) -> int:
        """Execute full ETL pipeline. Returns execution_id."""
        project = self.project_repo.get_with_details(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found.")

        # Find environment config
        env = next(
            (e for e in project.environments if e.env_type == env_type),
            None,
        )
        if not env:
            raise ValueError(f"Environment {env_type.value} not configured.")

        # Get connection string
        conn_str = ""
        if env.connection_id:
            conn_str = self.conn_svc.get_connection_string(env.connection_id)

        # Create execution record
        from etl_app.core.models.execution import ExecutionRecord
        record = ExecutionRecord(
            project_id=project_id,
            environment=env_type.value,
            status=ExecutionStatus.RUNNING,
            is_dry_run=is_dry_run,
        )
        self.exec_repo.create(record)
        exec_id = record.id

        self.exec_repo.add_log(exec_id, "INFO",
                                f"Starting ETL pipeline for '{project.name}' "
                                f"[{env_type.value}]{'[DRY RUN]' if is_dry_run else ''}")

        # Build shared context
        context = {
            "project_name": project.name,
            "environment": env_type.value,
            "staging_schema": env.staging_schema,
            "ods_schema": env.ods_schema,
            "dim_schema": env.dim_schema,
            "fact_schema": env.fact_schema,
            "output_path": env.get_output_path(),
            "all_previous_success": True,
        }

        # Ordered step execution
        step_classes = {
            StepType.INGESTION: IngestionStep,
            StepType.STAGING: StagingStep,
            StepType.ODS: OdsStep,
            StepType.DIMENSION: DimensionStep,
            StepType.FACT: FactStep,
            StepType.POST_PROCESSING: PostProcessingStep,
        }

        step_results = {}
        total_rows = 0

        for step in sorted(project.steps, key=lambda s: s.order):
            step_type_enum = StepType(step.step_type)
            step_cls = step_classes.get(step_type_enum)
            if not step_cls:
                continue

            config = step.config or {}
            if not config and step_type_enum not in (StepType.POST_PROCESSING,):
                self.exec_repo.add_log(exec_id, "WARNING",
                                        f"Step '{step.step_type}' has no config, skipping.",
                                        step.step_type)
                continue

            self.exec_repo.add_log(exec_id, "INFO",
                                    f"▶ Running step: {step.name}", step.step_type)
            try:
                step_instance = step_cls(conn_str=conn_str, is_dry_run=is_dry_run)
                result = step_instance.execute(config, context)

                step_results[step.step_type] = result.to_dict()
                total_rows += result.rows

                if result.success:
                    self.exec_repo.add_log(
                        exec_id, "INFO",
                        f"✓ {step.name}: {result.message}",
                        step.step_type,
                        {"rows": result.rows, **result.details},
                    )
                else:
                    context["all_previous_success"] = False
                    self.exec_repo.add_log(
                        exec_id, "ERROR",
                        f"✗ {step.name}: {result.message}",
                        step.step_type,
                    )

            except Exception as e:
                context["all_previous_success"] = False
                logger.exception(f"Unexpected error in step {step.step_type}: {e}")
                self.exec_repo.add_log(exec_id, "ERROR",
                                        f"✗ Unexpected error in {step.name}: {e}",
                                        step.step_type)
                step_results[step.step_type] = {"success": False, "error": str(e)}

        # Finalize
        final_status = (
            ExecutionStatus.DRY_RUN if is_dry_run
            else (ExecutionStatus.SUCCESS if context["all_previous_success"]
                  else ExecutionStatus.FAILED)
        )
        record = self.exec_repo.get(exec_id)
        record.status = final_status
        record.finished_at = datetime.utcnow()
        record.duration_seconds = (
            (record.finished_at - record.started_at).total_seconds()
        )
        record.rows_processed = total_rows
        record.step_results = step_results
        self.exec_repo.update(record)

        self.exec_repo.add_log(
            exec_id, "INFO",
            f"Pipeline finished: {final_status.value} | {total_rows:,} rows | "
            f"{record.duration_seconds:.1f}s",
        )
        return exec_id
