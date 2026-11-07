import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import get_settings

settings = get_settings()


class StorageService:
    """Handles file upload and retrieval. Currently local disk; swap to S3 later."""

    def __init__(self):
        self.base_path = Path(settings.storage_local_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project_id: str) -> Path:
        path = self.base_path / project_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def save_upload(self, project_id: str, file: UploadFile, subfolder: str = "uploads") -> str:
        """Save an uploaded file and return its relative path."""
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        content = await file.read()
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum size of {settings.max_file_size_mb} MB",
            )

        ext = Path(file.filename).suffix if file.filename else ""
        filename = f"{uuid.uuid4().hex}{ext}"
        dest_dir = self._project_dir(project_id) / subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename

        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)

        return str(dest.relative_to(self.base_path))

    async def save_bytes(self, project_id: str, data: bytes, filename: str, subfolder: str = "output") -> str:
        """Save raw bytes (e.g. generated video) and return relative path."""
        dest_dir = self._project_dir(project_id) / subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename

        async with aiofiles.open(dest, "wb") as f:
            await f.write(data)

        return str(dest.relative_to(self.base_path))

    def get_full_path(self, relative_path: str) -> Path:
        return self.base_path / relative_path

    def delete_file(self, relative_path: str) -> bool:
        full = self.get_full_path(relative_path)
        if full.exists():
            full.unlink()
            return True
        return False

