import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["USSM"])

_node_reference = None


def set_node(node):
    global _node_reference
    _node_reference = node


@router.get("/api/ussm/sensors")
def get_active_sensors():
    if _node_reference and hasattr(_node_reference, "active_sensors"):
        return {"active_sensors": _node_reference.active_sensors}
    return {"active_sensors": []}


@router.websocket("/ws/ussms")
async def websocket_ussm(websocket: WebSocket):
    await websocket.accept()
    try:
        last_msg_id = None
        while True:
            if _node_reference and hasattr(_node_reference, "ussm_data"):
                current_data = _node_reference.ussm_data
                current_id = getattr(_node_reference, "ussm_id", 0)

                if current_id != last_msg_id:
                    await websocket.send_json(current_data)
                    last_msg_id = current_id

            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        pass
