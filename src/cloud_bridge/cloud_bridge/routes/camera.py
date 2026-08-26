import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["Camera"])

_node_reference = None


def set_node(node):
    global _node_reference
    _node_reference = node


@router.websocket("/ws/camera/{cam_name}")
async def websocket_camera(websocket: WebSocket, cam_name: str):
    await websocket.accept()
    try:
        last_frame_id = None
        while True:
            if _node_reference:
                if cam_name == "button":
                    frame = getattr(_node_reference, "cam_button_frame", None)
                    frame_id = getattr(_node_reference, "cam_button_id", 0)
                elif cam_name == "top":
                    frame = getattr(_node_reference, "cam_top_frame", None)
                    frame_id = getattr(_node_reference, "cam_top_id", 0)
                else:
                    break

                if frame and frame_id != last_frame_id:
                    if frame and frame_id != last_frame_id:
                        try:
                            await websocket.send_bytes(frame)
                            last_frame_id = frame_id
                        except Exception:
                            break

            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        pass
