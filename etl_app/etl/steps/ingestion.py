"""Step 1 - CSV Ingestion."""
from typing import Dict, Any
from pathlib import Path
from loguru import logger
from .base import BaseStep, StepResult


class IngestionStep(BaseStep):
    def execute(self, config: dict, context: dict) -> StepResult:
        file_path = config.get("file_path") or context.get("file_path")
        if not file_path:
            return StepResult(False, message="No file path configured.")

        path = Path(file_path)
        if not path.exists():
            return StepResult(False, message=f"File not found: {file_path}")

        delimiter = config.get("delimiter", ";")
        encoding = config.get("encoding", "utf-8-sig")
        has_header = config.get("has_header", True)

        try:
            import pandas as pd
            df = pd.read_csv(
                path,
                sep=delimiter,
                encoding=encoding,
                header=0 if has_header else None,
                dtype=str,
                keep_default_na=False,
            )
            rows = len(df)
            columns = list(df.columns)
            logger.info(f"Ingestion: {rows} rows, {len(columns)} columns from {path.name}")

            # Store in context for next steps
            context["dataframe"] = df
            context["source_columns"] = columns
            context["source_file"] = str(path)
            context["source_rows"] = rows

            return StepResult(
                success=True,
                rows=rows,
                message=f"Loaded {rows:,} rows from {path.name}",
                details={"columns": columns, "file": path.name},
            )
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return StepResult(False, message=str(e))
