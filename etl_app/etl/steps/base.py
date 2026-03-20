"""Base ETL step with shared utilities."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger


class StepResult:
    def __init__(self, success: bool, rows: int = 0,
                 message: str = "", details: dict = None):
        self.success = success
        self.rows = rows
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "rows": self.rows,
            "message": self.message,
            "details": self.details,
        }


class BaseStep(ABC):
    def __init__(self, conn_str: str, is_dry_run: bool = False):
        self.conn_str = conn_str
        self.is_dry_run = is_dry_run

    def _get_connection(self):
        import pyodbc
        return pyodbc.connect(self.conn_str)

    def _execute_sql(self, sql: str, conn=None) -> int:
        """Execute SQL and return affected rows."""
        close_after = conn is None
        if conn is None:
            conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if self.is_dry_run:
                logger.debug(f"[DRY RUN] SQL:\n{sql[:500]}")
                return 0
            cursor.execute(sql)
            conn.commit()
            return cursor.rowcount
        finally:
            if close_after:
                conn.close()

    def _table_exists(self, schema: str, table: str, conn=None) -> bool:
        sql = (
            f"SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
            f"WHERE TABLE_SCHEMA='{schema}' AND TABLE_NAME='{table}'"
        )
        close_after = conn is None
        if conn is None:
            conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.fetchone() is not None
        finally:
            if close_after:
                conn.close()

    def _drop_and_create_table(self, schema: str, table: str,
                                 columns_ddl: str, conn) -> None:
        drop = f"IF OBJECT_ID('{schema}.{table}', 'U') IS NOT NULL DROP TABLE [{schema}].[{table}]"
        create = f"CREATE TABLE [{schema}].[{table}] ({columns_ddl})"
        cursor = conn.cursor()
        cursor.execute(drop)
        cursor.execute(create)
        conn.commit()

    @abstractmethod
    def execute(self, config: dict, context: dict) -> StepResult:
        pass
