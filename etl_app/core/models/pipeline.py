"""Pipeline step models."""
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean,
    ForeignKey, Text, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from etl_app.database.base import Base


class StepType(str, enum.Enum):
    INGESTION = "ingestion"
    STAGING = "staging"
    ODS = "ods"
    DIMENSION = "dimension"
    FACT = "fact"
    POST_PROCESSING = "post_processing"


class StepStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIGURED = "configured"
    VALID = "valid"
    ERROR = "error"


class PipelineStep(Base):
    __tablename__ = "pipeline_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    step_type = Column(SAEnum(StepType), nullable=False)
    order = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    status = Column(SAEnum(StepStatus), default=StepStatus.PENDING)
    config = Column(JSON, nullable=True)  # Step-specific config as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    project = relationship("Project", back_populates="steps")

    def __repr__(self) -> str:
        return f"<PipelineStep(type={self.step_type}, order={self.order})>"


# ── Pydantic schemas for step configs (not ORM, used for validation/serialization) ──

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class CsvConfig(BaseModel):
    file_path: Optional[str] = None
    delimiter: str = ";"
    encoding: str = "utf-8-sig"
    has_header: bool = True
    skip_rows: int = 0
    detected_columns: List[str] = []
    sample_rows: int = 100


class ColumnMapping(BaseModel):
    source_column: str
    target_column: str
    source_type: Optional[str] = None
    target_type: Optional[str] = None
    target_size: Optional[int] = None
    is_nullable: bool = True
    is_index: bool = False
    transformation: Optional[str] = None  # Python/SQL expression


class CalculatedColumn(BaseModel):
    name: str
    expression: str
    expression_type: Literal["python", "sql"] = "python"
    output_type: Optional[str] = None
    description: Optional[str] = None


class StagingConfig(BaseModel):
    table_name: str = ""
    csv_config: CsvConfig = Field(default_factory=CsvConfig)
    selected_columns: List[str] = []
    truncate_before_load: bool = True
    batch_size: int = 1000


class FilterConfig(BaseModel):
    expression: str = ""
    expression_type: Literal["python", "sql"] = "python"


class OdsConfig(BaseModel):
    table_name: str = ""
    source_staging_table: str = ""
    column_mappings: List[ColumnMapping] = []
    calculated_columns: List[CalculatedColumn] = []
    filters: List[FilterConfig] = []
    index_columns: List[str] = []
    truncate_before_load: bool = True


class DimensionConfig(BaseModel):
    table_name: str = ""
    source_ods_table: str = ""
    use_surrogate_key: bool = True
    surrogate_key_column: str = "sk_id"
    load_mode: Literal["insert", "merge"] = "insert"
    business_key_columns: List[str] = []
    tracked_columns: List[str] = []
    selected_columns: List[str] = []


class JoinConfig(BaseModel):
    dimension_table: str
    dimension_schema: str = "dim"
    join_keys: List[dict] = []  # [{"source": "col1", "dimension": "col2"}]
    surrogate_key_column: str = "sk_id"
    alias: Optional[str] = None


class FactConfig(BaseModel):
    table_name: str = ""
    source_ods_table: str = ""
    joins: List[JoinConfig] = []
    selected_columns: List[str] = []
    load_mode: Literal["insert", "merge"] = "insert"
    business_key_columns: List[str] = []
