import psutil
from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["System"])

_node_reference = None


def set_node_reference(node):
    global _node_reference
    _node_reference = node


@router.get("/values")
def get_system_values():
    if _node_reference and hasattr(_node_reference, "get_sys_values"):
        return {"system_values": _node_reference.get_sys_values()}

    try:
        return {
            "system_values": {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory": dict(psutil.virtual_memory()._asdict()),
            }
        }
    except Exception:
        return {"system_values": {}}


@router.get("/bms")
def get_bms_values():
    if _node_reference and hasattr(_node_reference, "get_bms_values"):
        return {"bms_values": _node_reference.get_bms_values()}

    return {"bms_values": {"voltage": 0.0, "percentage": 0.0}}
