"""
Video Service — manages AI video generation, batch clip rendering,
job polling, download caching, and failure recovery.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from bson import ObjectId
from fastapi import HTTPException
import logging

from app.database import get_db
from app.services.storage_service import StorageService
from app.services.video_providers.factory import get_video_provider
from app.models.video import (
    VideoClip,
    VideoProviderType,
    ClipStatus,
    GenerateClipsRequest,
    RegenerateClipRequest,
)

logger = logging.getLogger(__name__)


class VideoService:
    """Manages AI video generation workflow for storyboard scenes."""

    def __init__(self):
        self.storage = StorageService()

    def _collection(self):
        return get_db()["video_clips"]

    def _serialize(self, doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def generate_clips_for_storyboard(self, request: GenerateClipsRequest) -> List[dict]:
        """
        Submits and generates video clips for each scene in the storyboard.
        Supports partial or full storyboard scene generation.
        """
        db = get_db()
        if not ObjectId.is_valid(request.storyboard_id):
            raise HTTPException(status_code=400, detail="Invalid storyboard ID")

        storyboard = await db["storyboards"].find_one({"_id": ObjectId(request.storyboard_id)})
        if not storyboard:
            raise HTTPException(status_code=404, detail="Storyboard not found")

        scenes = storyboard.get("scenes", [])
        if request.scene_numbers:
            scenes = [s for s in scenes if s.get("scene_number") in request.scene_numbers]

        if not scenes:
            raise HTTPException(status_code=400, detail="No matching scenes to generate")

        provider = get_video_provider(request.provider)
        created_clips = []
        now = datetime.now(timezone.utc)

        for scene in scenes:
            scene_num = scene.get("scene_number", 1)
            prompt = scene.get("visual_prompt", "")
            neg_prompt = scene.get("negative_prompt")
            duration = scene.get("duration_seconds", 5)
            aspect_ratio = storyboard.get("aspect_ratio", "16:9")
            motion = scene.get("motion_strength", 5)

            # Insert initial record
            clip_doc = {
                "project_id": request.project_id,
                "storyboard_id": request.storyboard_id,
                "scene_number": scene_num,
                "provider": request.provider.value,
                "external_task_id": None,
                "status": ClipStatus.PROCESSING.value,
                "progress": 10,
                "prompt_used": prompt,
                "negative_prompt_used": neg_prompt,
                "video_url": None,
                "local_file_path": None,
                "thumbnail_url": None,
                "duration_seconds": float(duration),
                "file_size_bytes": None,
                "error_message": None,
                "retry_count": 0,
                "created_at": now,
                "updated_at": now,
            }

            result = await self._collection().insert_one(clip_doc)
            clip_id = str(result.inserted_id)

            try:
                # 1. Submit to provider
                task_id = await provider.submit_prompt(
                    prompt=prompt,
                    negative_prompt=neg_prompt,
                    duration_seconds=duration,
                    aspect_ratio=aspect_ratio,
                    motion_strength=motion,
                )

                # 2. Poll initial status
                status_info = await provider.poll_status(task_id)
                video_url = status_info.get("video_url")
                is_completed = status_info.get("status") == "completed" and video_url

                local_path = None
                file_size = None

                # 3. If completed immediately (e.g. Mock or fast provider), download and cache
                if is_completed:
                    clip_bytes = await provider.fetch_video_bytes(video_url)
                    filename = f"scene_{scene_num}.mp4"
                    local_path = await self.storage.save_bytes(
                        project_id=request.project_id,
                        data=clip_bytes,
                        filename=filename,
                        subfolder="clips",
                    )
                    file_size = len(clip_bytes)

                update_fields = {
                    "external_task_id": task_id,
                    "status": ClipStatus.COMPLETED.value if is_completed else ClipStatus.PROCESSING.value,
                    "progress": 100 if is_completed else status_info.get("progress", 25),
                    "video_url": video_url or f"/files/{request.project_id}/download/{local_path}" if local_path else None,
                    "local_file_path": local_path,
                    "file_size_bytes": file_size,
                    "updated_at": datetime.now(timezone.utc),
                }

                await self._collection().update_one(
                    {"_id": ObjectId(clip_id)},
                    {"$set": update_fields},
                )

            except Exception as e:
                logger.error(f"Failed generating clip for scene {scene_num}: {e}")
                await self._collection().update_one(
                    {"_id": ObjectId(clip_id)},
                    {
                        "$set": {
                            "status": ClipStatus.FAILED.value,
                            "error_message": str(e),
                            "updated_at": datetime.now(timezone.utc),
                        }
                    },
                )

            saved = await self._collection().find_one({"_id": ObjectId(clip_id)})
            created_clips.append(self._serialize(saved))

        return created_clips

    async def get_clip_by_id(self, clip_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(clip_id):
            return None
        doc = await self._collection().find_one({"_id": ObjectId(clip_id)})
        return self._serialize(doc) if doc else None

    async def get_clips_by_project(self, project_id: str) -> List[dict]:
        cursor = self._collection().find({"project_id": project_id}).sort("scene_number", 1)
        return [self._serialize(doc) async for doc in cursor]

    async def regenerate_clip(self, clip_id: str, request: RegenerateClipRequest) -> dict:
        """Regenerate a single scene clip with updated prompt or provider."""
        clip = await self.get_clip_by_id(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Video clip not found")

        provider_type = request.provider or VideoProviderType(clip.get("provider", "mock"))
        provider = get_video_provider(provider_type)

        prompt = request.prompt_override or clip["prompt_used"]
        neg_prompt = request.negative_prompt_override or clip.get("negative_prompt_used")
        duration = int(clip.get("duration_seconds", 5))

        try:
            task_id = await provider.submit_prompt(
                prompt=prompt,
                negative_prompt=neg_prompt,
                duration_seconds=duration,
            )

            status_info = await provider.poll_status(task_id)
            video_url = status_info.get("video_url")
            is_completed = status_info.get("status") == "completed" and video_url

            local_path = None
            file_size = None
            if is_completed:
                clip_bytes = await provider.fetch_video_bytes(video_url)
                filename = f"scene_{clip['scene_number']}_v{clip.get('retry_count', 0) + 1}.mp4"
                local_path = await self.storage.save_bytes(
                    project_id=clip["project_id"],
                    data=clip_bytes,
                    filename=filename,
                    subfolder="clips",
                )
                file_size = len(clip_bytes)

            updates = {
                "provider": provider_type.value,
                "external_task_id": task_id,
                "prompt_used": prompt,
                "negative_prompt_used": neg_prompt,
                "status": ClipStatus.COMPLETED.value if is_completed else ClipStatus.PROCESSING.value,
                "progress": 100 if is_completed else status_info.get("progress", 25),
                "video_url": video_url or f"/files/{clip['project_id']}/download/{local_path}" if local_path else None,
                "local_file_path": local_path,
                "file_size_bytes": file_size,
                "error_message": None,
                "retry_count": clip.get("retry_count", 0) + 1,
                "updated_at": datetime.now(timezone.utc),
            }

            await self._collection().update_one(
                {"_id": ObjectId(clip_id)},
                {"$set": updates},
            )

        except Exception as e:
            await self._collection().update_one(
                {"_id": ObjectId(clip_id)},
                {
                    "$set": {
                        "status": ClipStatus.FAILED.value,
                        "error_message": str(e),
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            raise HTTPException(status_code=500, detail=f"Clip regeneration failed: {str(e)}")

        updated = await self.get_clip_by_id(clip_id)
        return updated
