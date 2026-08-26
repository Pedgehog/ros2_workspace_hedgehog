from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Database"])

_node_reference = None


def set_node(node):
    global _node_reference
    _node_reference = node


class DatabaseRequest(BaseModel):
    db_name: str


@router.get("/api/database/list")
def list_databases():
    if _node_reference and hasattr(_node_reference, "list_databases"):
        return _node_reference.list_databases()
    return {"databases": [], "active_database": ""}


@router.post("/api/database/manage")
def create_database(req: DatabaseRequest):
    if _node_reference and hasattr(_node_reference, "create_database"):
        success = _node_reference.create_database(req.db_name)
        if success:
            return {"status": "success", "message": f"Database {req.db_name} created"}
        raise HTTPException(status_code=400, detail="Could not create database")
    raise HTTPException(status_code=500, detail="Node not connected or method missing")


@router.post("/api/database/select")
def select_database(req: DatabaseRequest):
    if _node_reference and hasattr(_node_reference, "select_database"):
        success = _node_reference.select_database(req.db_name)
        if success:
            return {
                "status": "success",
                "message": f"Active database set to {req.db_name}",
            }
        raise HTTPException(status_code=400, detail="Could not select database")
    raise HTTPException(status_code=500, detail="Node not connected or method missing")
