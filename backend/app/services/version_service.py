"""
Video Version Management & Scene Splicing Service.
Enables instant non-destructive scene regeneration, multi-version history, and rollbacks.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from bson import ObjectId
from fastapi import HTTPException
import logging

from app.database import get_db
from app.services.storage_service import StorageService
from app.services.video_service import VideoService
from app.services.production_service import ProductionService
from app.models.quality import VideoVersion, SpliceSceneRequest
from app.models.video import RegenerateClipRequest
from app.models.production import StartRenderRequest

logger = logging.getLogger(__name__)


class VersionService:
    """Manages video versions (v1, v2...) and one-click scene splicing."""

    def __init__(self):
        self.storage = StorageService()
        self.video_service = VideoService()
        self.production_service = ProductionService()

    def _collection(self):
        return get_db()["video_versions"]

    def _serialize(self, doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def record_version(
        self,
        project_id: str,
        label: str,
        video_path: str,
        video_url: str,
        duration_seconds: float,
        file_size_bytes: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Saves a new video render version and sets it as active."""
        # Find highest version number
        cursor = self._collection().find({"project_id": project_id}).sort("version_number", -1).limit(1)
        latest = [c async for c in cursor]
        next_version = (latest[0]["version_number"] + 1) if latest else 1

        now = datetime.now(timezone.utc)
        # Mark previous versions as inactive
        await self._collection().update_many(
            {"project_id": project_id},
            {"$set": {"is_active": False, "updated_at": now}}
        )

        doc = {
            "project_id": project_id,
            "version_number": next_version,
            "label": label or f"Version {next_version}",
            "video_path": video_path,
            "video_url": video_url,
            "duration_seconds": float(duration_seconds),
            "file_size_bytes": file_size_bytes,
            "is_active": True,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
        }

        result = await self._collection().insert_one(doc)
        created = await self._collection().find_one({"_id": result.inserted_id})
        return self._serialize(created)

    async def list_versions(self, project_id: str) -> List[dict]:
        """Lists all versions recorded for a project."""
        cursor = self._collection().find({"project_id": project_id}).sort("version_number", -1)
        return [self._serialize(doc) async for doc in cursor]

    async def activate_version(self, project_id: str, version_number: int) -> dict:
        """Rollback or set active video version."""
        db = get_db()
        target = await self._collection().find_one({"project_id": project_id, "version_number": version_number})
        if not target:
            raise HTTPException(status_code=404, detail=f"Version {version_number} not found")

        now = datetime.now(timezone.utc)
        # Deactivate all
        await self._collection().update_many(
            {"project_id": project_id},
            {"$set": {"is_active": False, "updated_at": now}}
        )
        # Activate target
        await self._collection().update_one(
            {"_id": target["_id"]},
            {"$set": {"is_active": True, "updated_at": now}}
        )

        # Update main Project document output URL
        await db["projects"].update_one(
            {"_id": ObjectId(project_id)},
            {
                "$set": {
                    "output_video_url": target["video_url"],
                    "duration_actual": target["duration_seconds"],
                    "updated_at": now,
                }
            }
        )

        updated = await self._collection().find_one({"_id": target["_id"]})
        return self._serialize(updated)

    async def splice_scene_and_rerender(self, request: SpliceSceneRequest) -> dict:
        """
        Targeted scene replacement:
        1. Regenerates ONLY the specified scene clip.
        2. Re-assembles the master video with FFmpeg.
        3. Saves as a new version (e.g. v2: Spliced Scene 2).
        """
        db = get_db()
        # Find clip for this scene
        clip = await db["video_clips"].find_one({
            "project_id": request.project_id,
            "scene_number": request.scene_number,
        })

        if not clip:
            raise HTTPException(
                status_code=404,
                detail=f"Clip for scene {request.scene_number} not found in project"
            )

        # 1. Regenerate single clip
        regen_req = RegenerateClipRequest(prompt_override=request.new_prompt)
        await self.video_service.regenerate_clip(str(clip["_id"]), regen_req)

        # 2. Re-render master video using updated clip + existing clips
        render_req = StartRenderRequest(
            project_id=request.project_id,
            storyboard_id=request.storyboard_id,
        )
        job = await self.production_service.create_render_job(render_req)

        # 3. Record new version
        label = request.version_label or f"Scene {request.scene_number} Spliced"
        version_doc = await self.record_version(
            project_id=request.project_id,
            label=label,
            video_path=job.get("output_video_path", ""),
            video_url=job.get("output_video_url", ""),
            duration_seconds=job.get("duration_seconds", 0.0),
            file_size_bytes=job.get("file_size_bytes", 0),
            metadata={"spliced_scene": request.scene_number},
        )

        return {
            "version": version_doc,
            "render_job": job,
        }
