import os
from ament_index_python.packages import get_package_share_directory
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_node_reference = None


def set_node(node):
    global _node_reference
    _node_reference = node


@router.get("/", response_class=HTMLResponse)
def serve_homepage():
    try:
        share_dir = get_package_share_directory("cloud_bridge")
        html_path = os.path.join(share_dir, "web", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<h1>Error loading webpage</h1><p>{str(e)}</p>"


@router.get("/api/status")
def api_status():
    if _node_reference:
        battery_data = {
            "voltage": _node_reference.battery_voltage,
            "percentage": _node_reference.battery_percentage,
        }
    else:
        battery_data = "Node not connected"

    return {"status": "online", "battery": battery_data}
