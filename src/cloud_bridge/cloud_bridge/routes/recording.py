from fastapi import APIRouter

router = APIRouter(prefix="/api/recording", tags=["Recording"])

_node_reference = None


def set_node(node):
    global _node_reference
    _node_reference = node


@router.post("/start")
def start_recording():
    if _node_reference and hasattr(_node_reference, "start_recording"):
        _node_reference.start_recording()
        return {"status": "success", "message": "Recording started"}
    return {"status": "error", "message": "Node not connected or method missing"}


@router.post("/stop")
def stop_recording():
    if _node_reference and hasattr(_node_reference, "stop_recording"):
        _node_reference.stop_recording()
        return {"status": "success", "message": "Recording stopped"}
    return {"status": "error", "message": "Node not connected or method missing"}
