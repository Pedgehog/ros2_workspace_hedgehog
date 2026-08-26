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


@router.post("/trigger")
def trigger_recording():
    if _node_reference and hasattr(_node_reference, "trigger_recording"):
        _node_reference.trigger_recording()
        return {"status": "success", "message": "Recording triggered"}
    return {"status": "error", "message": "Node not connected or method missing"}


@router.get("/status")
def get_recording_status():
    if _node_reference and hasattr(_node_reference, "is_recording"):
        status = (
            _node_reference.is_recording()
            if callable(_node_reference.is_recording)
            else _node_reference.is_recording
        )
        return {"status": "success", "is_recording": status}
    return {"status": "error", "message": "Node not connected or status missing"}
