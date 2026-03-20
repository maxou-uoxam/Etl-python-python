"""Database connection API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from etl_app.database import get_db
from etl_app.core.services.connection_service import ConnectionService

router = APIRouter(prefix="/api/connections", tags=["Connections"])


class ConnectionCreate(BaseModel):
    name: str
    server: str
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    use_windows_auth: bool = False
    port: int = 1433


class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    server: Optional[str] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    use_windows_auth: Optional[bool] = None
    port: Optional[int] = None


@router.get("/")
def list_connections(db: Session = Depends(get_db)):
    svc = ConnectionService(db)
    conns = svc.list_connections()
    return [
        {
            "id": c.id,
            "name": c.name,
            "server": c.server,
            "database": c.database,
            "use_windows_auth": c.use_windows_auth,
            "port": c.port,
        }
        for c in conns
    ]


@router.post("/", status_code=201)
def create_connection(data: ConnectionCreate, db: Session = Depends(get_db)):
    svc = ConnectionService(db)
    try:
        conn = svc.create_connection(**data.dict())
        return {"id": conn.id, "name": conn.name, "message": "Connection created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{connection_id}")
def get_connection(connection_id: int, db: Session = Depends(get_db)):
    svc = ConnectionService(db)
    conn = svc.get_connection(connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {
        "id": conn.id,
        "name": conn.name,
        "server": conn.server,
        "database": conn.database,
        "username": conn.username,
        "use_windows_auth": conn.use_windows_auth,
        "port": conn.port,
    }


@router.put("/{connection_id}")
def update_connection(connection_id: int, data: ConnectionUpdate,
                       db: Session = Depends(get_db)):
    svc = ConnectionService(db)
    try:
        updates = {k: v for k, v in data.dict().items() if v is not None}
        conn = svc.update_connection(connection_id, **updates)
        return {"id": conn.id, "name": conn.name, "message": "Connection updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{connection_id}", status_code=204)
def delete_connection(connection_id: int, db: Session = Depends(get_db)):
    svc = ConnectionService(db)
    if not svc.delete_connection(connection_id):
        raise HTTPException(status_code=404, detail="Connection not found")


@router.post("/{connection_id}/test")
def test_connection(connection_id: int, db: Session = Depends(get_db)):
    svc = ConnectionService(db)
    return svc.test_connection(connection_id)


@router.get("/{connection_id}/databases")
def list_databases(connection_id: int, db: Session = Depends(get_db)):
    svc = ConnectionService(db)
    return svc.get_databases(connection_id)
