"""Step 3 - ODS transformation (schema 'ods')."""
import pandas as pd
from loguru import logger
from .base import BaseStep, StepResult


class OdsStep(BaseStep):
    def execute(self, config: dict, context: dict) -> StepResult:
        table_name = config.get("table_name")
        if not table_name:
            return StepResult(False, message="No ODS table name configured.")

        ods_schema = context.get("ods_schema", "ods")
        df: pd.DataFrame = context.get("staging_dataframe")
        if df is None:
            return StepResult(False, message="No staging data in context.")

        try:
            # Apply column mappings (rename)
            mappings = config.get("column_mappings", [])
            rename_map = {}
            for m in mappings:
                src = m.get("source_column")
                tgt = m.get("target_column")
                if src and tgt and src in df.columns:
                    rename_map[src] = tgt
            if rename_map:
                df = df.rename(columns=rename_map)

            # Apply Python filters
            for f in config.get("filters", []):
                expr = f.get("expression", "")
                expr_type = f.get("expression_type", "python")
                if expr and expr_type == "python":
                    df = df.query(expr)

            # Add calculated columns
            for calc in config.get("calculated_columns", []):
                name = calc.get("name")
                expr = calc.get("expression", "")
                expr_type = calc.get("expression_type", "python")
                if name and expr and expr_type == "python":
                    df[name] = df.eval(expr)

            # Select final columns
            selected = config.get("selected_columns") or list(df.columns)
            df = df[[c for c in selected if c in df.columns]]

            if self.is_dry_run:
                context["ods_dataframe"] = df
                context["ods_table"] = f"{ods_schema}.{table_name}"
                return StepResult(True, rows=len(df),
                                  message=f"[DRY RUN] ODS transform: {len(df):,} rows")

            conn = self._get_connection()
            cursor = conn.cursor()

            # Build typed DDL from detected types / config
            col_types = {m.get("target_column", m.get("source_column")): m
                         for m in mappings}
            cols_ddl = self._build_ods_ddl(df, col_types, config)
            self._drop_and_create_table(ods_schema, table_name, cols_ddl, conn)

            # Insert
            placeholders = ", ".join(["?"] * len(df.columns))
            col_names = ", ".join(f"[{c}]" for c in df.columns)
            insert_sql = (
                f"INSERT INTO [{ods_schema}].[{table_name}] ({col_names}) "
                f"VALUES ({placeholders})"
            )
            batch_size = 1000
            total = 0
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                rows = [tuple(r) for r in batch.values]
                cursor.executemany(insert_sql, rows)
                conn.commit()
                total += len(rows)

            # Create indexes
            for idx_col in config.get("index_columns", []):
                if idx_col in df.columns:
                    idx_name = f"IX_{table_name}_{idx_col}"
                    idx_sql = (
                        f"CREATE NONCLUSTERED INDEX [{idx_name}] "
                        f"ON [{ods_schema}].[{table_name}] ([{idx_col}])"
                    )
                    cursor.execute(idx_sql)
            conn.commit()
            conn.close()

            context["ods_dataframe"] = df
            context["ods_table"] = f"{ods_schema}.{table_name}"
            logger.info(f"ODS load complete: {total:,} rows → [{ods_schema}].[{table_name}]")
            return StepResult(True, rows=total,
                              message=f"Transformed {total:,} rows into ODS")
        except Exception as e:
            logger.error(f"ODS transform failed: {e}")
            return StepResult(False, message=str(e))

    def _build_ods_ddl(self, df: pd.DataFrame, col_types: dict,
                        config: dict) -> str:
        parts = []
        for col in df.columns:
            mapping = col_types.get(col, {})
            tgt_type = mapping.get("target_type", "VARCHAR")
            tgt_size = mapping.get("target_size")
            nullable = "NULL" if mapping.get("is_nullable", True) else "NOT NULL"

            if tgt_type in ("INT", "BIGINT", "BIT"):
                parts.append(f"[{col}] {tgt_type} {nullable}")
            elif tgt_type in ("DECIMAL", "FLOAT", "NUMERIC"):
                parts.append(f"[{col}] {tgt_type}(18,4) {nullable}")
            elif tgt_type in ("DATE", "DATETIME", "DATETIME2"):
                parts.append(f"[{col}] {tgt_type} {nullable}")
            else:
                size = tgt_size or 500
                parts.append(f"[{col}] NVARCHAR({size}) {nullable}")
        return ",\n  ".join(parts)

    def generate_sql(self, config: dict, staging_schema: str = "sta",
                      ods_schema: str = "ods") -> str:
        """Generate ODS transformation SQL."""
        staging_table = config.get("source_staging_table", "staging_table")
        ods_table = config.get("table_name", "ods_table")
        mappings = config.get("column_mappings", [])
        calcs = config.get("calculated_columns", [])
        filters = config.get("filters", [])

        select_parts = []
        for m in mappings:
            src = m.get("source_column", "")
            tgt = m.get("target_column", src)
            transform = m.get("transformation")
            if transform:
                select_parts.append(f"  {transform} AS [{tgt}]")
            elif src != tgt:
                select_parts.append(f"  [{src}] AS [{tgt}]")
            else:
                select_parts.append(f"  [{src}]")

        for calc in calcs:
            if calc.get("expression_type") == "sql":
                select_parts.append(
                    f"  {calc['expression']} AS [{calc['name']}]"
                )

        where_parts = [
            f.get("expression", "") for f in filters
            if f.get("expression_type") == "sql"
        ]

        select_clause = ",\n".join(select_parts) if select_parts else "  *"
        where_clause = f"\nWHERE {' AND '.join(where_parts)}" if where_parts else ""

        return f"""-- ============================================================
-- ODS Transformation: [{ods_schema}].[{ods_table}]
-- Source: [{staging_schema}].[{staging_table}]
-- Generated by ETL Manager
-- ============================================================

IF OBJECT_ID('{ods_schema}.{ods_table}', 'U') IS NOT NULL
    TRUNCATE TABLE [{ods_schema}].[{ods_table}];

INSERT INTO [{ods_schema}].[{ods_table}]
SELECT
{select_clause}
FROM [{staging_schema}].[{staging_table}]{where_clause};
"""
