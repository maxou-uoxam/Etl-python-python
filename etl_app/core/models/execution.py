"""Execution tracking models."""
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, Float,
    ForeignKey, Text, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from etl_app.database.base import Base


class ExecutionStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DRY_RUN = "dry_run"


class ExecutionRecord(Base):
    __tablename__ = "execution_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    environment = Column(String(20), nullable=False)
    status = Column(SAEnum(ExecutionStatus), default=ExecutionStatus.RUNNING)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    rows_processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    is_dry_run = Column(Boolean, default=False)
    step_results = Column(JSON, nullable=True)  # Per-step stats

    # Relations
    project = relationship("Project", back_populates="executions")
    logs = relationship("ExecutionLog", back_populates="execution",
                        cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ExecutionRecord(id={self.id}, status={self.status})>"


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey("execution_records.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(20), default="INFO")  # DEBUG, INFO, WARNING, ERROR
    step_type = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)

    # Relations
    execution = relationship("ExecutionRecord", back_populates="logs")

    def __repr__(self) -> str:
        return f"<ExecutionLog(level={self.level}, message='{self.message[:50]}')>"


# Need to add Boolean import
from sqlalchemy import Boolean
