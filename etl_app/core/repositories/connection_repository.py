"""Database connection repository."""
from typing import Optional, List
from sqlalchemy.orm import Session
from etl_app.core.models.connection import DatabaseConnection, ConnectionType
from .base import BaseRepository


class ConnectionRepository(BaseRepository[DatabaseConnection]):
    def __init__(self, db: Session):
        super().__init__(DatabaseConnection, db)

    def get_by_name(self, name: str) -> Optional[DatabaseConnection]:
        return (
            self.db.query(DatabaseConnection)
            .filter(DatabaseConnection.name == name)
            .first()
        )

    def get_by_type(self, conn_type: ConnectionType) -> List[DatabaseConnection]:
        return (
            self.db.query(DatabaseConnection)
            .filter(DatabaseConnection.connection_type == conn_type)
            .all()
        )
