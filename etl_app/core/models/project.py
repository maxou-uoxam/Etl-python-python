"""Project domain model."""
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean,
    ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from etl_app.database.base import Base


class EnvironmentType(str, enum.Enum):
    DEV = "DEV"
    PREPROD = "PREPROD"
    RECETTE = "RECETTE"
    PROD = "PROD"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    yaml_path = Column(String(500), nullable=True)

    # Relations
    environments = relationship("ProjectEnvironment", back_populates="project",
                                cascade="all, delete-orphan")
    steps = relationship("PipelineStep", back_populates="project",
                         cascade="all, delete-orphan", order_by="PipelineStep.order")
    executions = relationship("ExecutionRecord", back_populates="project",
                              cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"


class ProjectEnvironment(Base):
    __tablename__ = "project_environments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    env_type = Column(SAEnum(EnvironmentType), nullable=False)

    # Source file config
    source_base_path = Column(String(500), nullable=True)
    source_product = Column(String(200), nullable=True)

    # Target DB connection
    connection_id = Column(Integer, ForeignKey("database_connections.id"), nullable=True)
    staging_schema = Column(String(100), default="sta")
    ods_schema = Column(String(100), default="ods")
    dim_schema = Column(String(100), default="dim")
    fact_schema = Column(String(100), default="fait")

    # Relations
    project = relationship("Project", back_populates="environments")
    connection = relationship("DatabaseConnection")

    def get_input_path(self) -> str:
        if self.source_base_path and self.source_product:
            return f"{self.source_base_path}/{self.env_type.value}/{self.source_product}/Entrée"
        return ""

    def get_output_path(self) -> str:
        if self.source_base_path and self.source_product:
            return f"{self.source_base_path}/{self.env_type.value}/{self.source_product}/Sortie"
        return ""
