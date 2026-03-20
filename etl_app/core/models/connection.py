"""Database connection model."""
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum as SAEnum
from etl_app.database.base import Base


class ConnectionType(str, enum.Enum):
    SQLSERVER = "sqlserver"
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class DatabaseConnection(Base):
    __tablename__ = "database_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    connection_type = Column(SAEnum(ConnectionType), default=ConnectionType.SQLSERVER)
    server = Column(String(500), nullable=True)
    port = Column(Integer, default=1433)
    database = Column(String(200), nullable=True)
    username = Column(String(200), nullable=True)
    password_encrypted = Column(String(500), nullable=True)  # Encrypted
    use_windows_auth = Column(Boolean, default=False)
    driver = Column(String(200), default="ODBC Driver 17 for SQL Server")
    extra_params = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_connection_string(self, password: str = "") -> str:
        if self.connection_type == ConnectionType.SQLSERVER:
            if self.use_windows_auth:
                return (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server},{self.port};"
                    f"DATABASE={self.database};"
                    "Trusted_Connection=yes;"
                )
            return (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={password};"
            )
        return ""

    def __repr__(self) -> str:
        return f"<DatabaseConnection(name='{self.name}', server='{self.server}')>"
