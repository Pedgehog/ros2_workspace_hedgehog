from pathlib import Path
import shutil
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/outputfiles", tags=["Output Files"])

_node_reference = None


def set_node(node):
    global _node_reference
    _node_reference = node


def get_output_dir() -> Path:
    output_path = Path.home() / "ros2_ws_hedgehog" / "output"
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


@router.get("/check")
def check_output_folder():
    try:
        output_dir = get_output_dir()
        if not output_dir.exists():
            return {"status": "error", "message": "Output directory does not exist"}

        files = [f.name for f in output_dir.iterdir() if f.is_file()]
        return {
            "status": "success",
            "directory_exists": True,
            "total_files": len(files),
            "files": files,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/download")
def download_entire_output_folder():
    output_dir = get_output_dir()

    if not output_dir.exists() or not any(output_dir.iterdir()):
        raise HTTPException(
            status_code=404, detail="Output directory is empty or does not exist"
        )

    archive_base_path = Path.home() / "ros2_ws_hedgehog" / "output_archive"

    try:
        archive_file = shutil.make_archive(
            base_name=str(archive_base_path), format="zip", root_dir=str(output_dir)
        )

        return FileResponse(
            path=archive_file,
            media_type="application/zip",
            filename="hedgehog_output_files.zip",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create archive: {str(e)}"
        )
