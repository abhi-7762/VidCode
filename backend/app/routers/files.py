from fastapi import APIRouter, UploadFile, File, HTTPException, Path as FPath
from fastapi.responses import FileResponse
from app.services.storage_service import StorageService

router = APIRouter(prefix="/files", tags=["Files"])


def get_storage() -> StorageService:
    return StorageService()


@router.post("/{project_id}/upload")
async def upload_file(
    project_id: str = FPath(..., description="Project ID"),
    file: UploadFile = File(...),
):
    """Upload a file (image, audio, etc.) for a project."""
    storage = get_storage()
    relative_path = await storage.save_upload(project_id, file)
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "stored_path": relative_path,
        "url": f"/files/{project_id}/download/{relative_path}",
    }


@router.get("/{project_id}/download/{file_path:path}")
async def download_file(project_id: str, file_path: str):
    """Download a stored file."""
    storage = get_storage()
    full_path = storage.get_full_path(file_path)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(full_path))

