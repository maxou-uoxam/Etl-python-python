"""Database connection service."""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from etl_app.core.models.connection import DatabaseConnection, ConnectionType
from etl_app.core.repositories import ConnectionRepository
from etl_app.core.services.encryption_service import EncryptionService


class ConnectionService:
    def __init__(self, db: Session):
        self.repo = ConnectionRepository(db)
        self.crypto = EncryptionService()

    def create_connection(self, name: str, server: str, database: str,
                           username: str = None, password: str = None,
                           use_windows_auth: bool = False,
                           port: int = 1433) -> DatabaseConnection:
        if self.repo.get_by_name(name):
            raise ValueError(f"Connection '{name}' already exists.")

        conn = DatabaseConnection(
            name=name,
            connection_type=ConnectionType.SQLSERVER,
            server=server,
            port=port,
            database=database,
            username=username,
            password_encrypted=self.crypto.encrypt(password) if password else None,
            use_windows_auth=use_windows_auth,
        )
        return self.repo.create(conn)

    def update_connection(self, connection_id: int, **kwargs) -> DatabaseConnection:
        conn = self.repo.get(connection_id)
        if not conn:
            raise ValueError(f"Connection {connection_id} not found.")

        if "password" in kwargs:
            conn.password_encrypted = self.crypto.encrypt(kwargs.pop("password"))

        for k, v in kwargs.items():
            if hasattr(conn, k):
                setattr(conn, k, v)

        return self.repo.update(conn)

    def delete_connection(self, connection_id: int) -> bool:
        return self.repo.delete(connection_id)

    def get_connection(self, connection_id: int) -> Optional[DatabaseConnection]:
        return self.repo.get(connection_id)

    def list_connections(self) -> List[DatabaseConnection]:
        return self.repo.get_all()

    def test_connection(self, connection_id: int) -> Dict[str, Any]:
        """Test SQL Server connection."""
        conn = self.repo.get(connection_id)
        if not conn:
            return {"success": False, "error": "Connection not found"}

        try:
            import pyodbc
            password = self.crypto.decrypt(conn.password_encrypted or "")
            conn_str = conn.get_connection_string(password)
            with pyodbc.connect(conn_str, timeout=10):
                pass
            return {"success": True, "message": "Connection successful"}
        except ImportError:
            return {"success": False, "error": "pyodbc not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_databases(self, connection_id: int) -> List[str]:
        """List available databases on the server."""
        conn = self.repo.get(connection_id)
        if not conn:
            return []
        try:
            import pyodbc
            password = self.crypto.decrypt(conn.password_encrypted or "")
            conn_str = conn.get_connection_string(password)
            with pyodbc.connect(conn_str, timeout=10) as cx:
                cursor = cx.cursor()
                cursor.execute("SELECT name FROM sys.databases ORDER BY name")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.warning(f"Could not list databases: {e}")
            return []

    def get_connection_string(self, connection_id: int) -> str:
        """Get decrypted connection string."""
        conn = self.repo.get(connection_id)
        if not conn:
            return ""
        password = self.crypto.decrypt(conn.password_encrypted or "")
        return conn.get_connection_string(password)
