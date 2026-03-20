"""Execution tracking repository."""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from etl_app.core.models.execution import ExecutionRecord, ExecutionLog, ExecutionStatus
from .base import BaseRepository


class ExecutionRepository(BaseRepository[ExecutionRecord]):
    def __init__(self, db: Session):
        super().__init__(ExecutionRecord, db)

    def get_for_project(self, project_id: int,
                         limit: int = 20) -> List[ExecutionRecord]:
        return (
            self.db.query(ExecutionRecord)
            .filter(ExecutionRecord.project_id == project_id)
            .order_by(ExecutionRecord.started_at.desc())
            .limit(limit)
            .all()
        )

    def get_running(self) -> List[ExecutionRecord]:
        return (
            self.db.query(ExecutionRecord)
            .filter(ExecutionRecord.status == ExecutionStatus.RUNNING)
            .all()
        )

    def get_with_logs(self, execution_id: int) -> Optional[ExecutionRecord]:
        return (
            self.db.query(ExecutionRecord)
            .options(joinedload(ExecutionRecord.logs))
            .filter(ExecutionRecord.id == execution_id)
            .first()
        )

    def add_log(self, execution_id: int, level: str,
                message: str, step_type: str = None,
                details: dict = None) -> ExecutionLog:
        log = ExecutionLog(
            execution_id=execution_id,
            level=level,
            message=message,
            step_type=step_type,
            details=details,
        )
        self.db.add(log)
        self.db.commit()
        return log

    def get_logs(self, execution_id: int,
                 level: str = None) -> List[ExecutionLog]:
        q = self.db.query(ExecutionLog).filter(
            ExecutionLog.execution_id == execution_id
        )
        if level:
            q = q.filter(ExecutionLog.level == level)
        return q.order_by(ExecutionLog.timestamp).all()
