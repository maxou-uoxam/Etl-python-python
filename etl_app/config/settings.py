"""Application settings with environment support."""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "ETL Manager"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")

    # Database
    database_url: str = Field(
        default=f"sqlite:///{BASE_DIR}/etl_manager.db",
        env="DATABASE_URL"
    )

    # Projects directory
    projects_dir: Path = Field(default=BASE_DIR / "projects", env="PROJECTS_DIR")

    # Security
    secret_key: str = Field(default="change-me-in-production-etl-secret-key", env="SECRET_KEY")
    connection_encryption_key: str = Field(
        default="etl-manager-fernet-key-change-in-prod",
        env="CONNECTION_ENCRYPTION_KEY"
    )

    # Server
    host: str = Field(default="127.0.0.1", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # SQL Server defaults
    sqlserver_driver: str = "ODBC Driver 17 for SQL Server"
    sqlserver_timeout: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
