"""
Storyboard Service — orchestrates scene planning, character consistency,
camera specifications, and generative video prompt compilation.
"""
from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
from fastapi import HTTPException

from app.database import get_db
from app.services.gemini_service import GeminiService
from app.models.storyboard import (
    Storyboard,
    StoryboardScene,
    StoryboardGenerateRequest,
    StoryboardSceneUpdate,
    AspectRatio,
)


class StoryboardService:
    """Manages storyboard generation and scene-level operations."""

    def _collection(self):
        return get_db()["storyboards"]

    def _serialize(self, doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def generate(self, request: StoryboardGenerateRequest) -> dict:
        """
        Takes a script and compiles a complete cinematic storyboard:
          1. Retrieve script
          2. Gemini extracts characters and designs filmable shots
          3. Save to MongoDB
          4. Link storyboard_id to project
        """
        db = get_db()
        # Step 1: Retrieve script
        if not ObjectId.is_valid(request.script_id):
            raise HTTPException(status_code=400, detail="Invalid script ID")

        script_doc = await db["scripts"].find_one({"_id": ObjectId(request.script_id)})
        if not script_doc:
            raise HTTPException(status_code=404, detail="Script not found")

        # Step 2: Gemini Storyboard generation
        gemini = GeminiService()
        theme = request.visual_theme or "cinematic, photorealistic, 8k resolution"
        aspect_ratio = request.aspect_ratio.value if isinstance(request.aspect_ratio, AspectRatio) else str(request.aspect_ratio)

        storyboard_data = await gemini.generate_storyboard(
            script_data=script_doc,
            visual_theme=theme,
            aspect_ratio=aspect_ratio,
        )

        scenes = storyboard_data.get("scenes", [])
        total_duration = sum(s.get("duration_seconds", 5) for s in scenes)

        now = datetime.now(timezone.utc)
        doc = {
            "project_id": request.project_id,
            "script_id": request.script_id,
            "aspect_ratio": aspect_ratio,
            "visual_theme": storyboard_data.get("visual_theme", theme),
            "characters": storyboard_data.get("characters", []),
            "scenes": scenes,
            "total_scenes": len(scenes),
            "total_duration_seconds": total_duration,
            "created_at": now,
            "updated_at": now,
        }

        result = await self._collection().insert_one(doc)
        created = await self._collection().find_one({"_id": result.inserted_id})

        # Update Project record
        if ObjectId.is_valid(request.project_id):
            await db["projects"].update_one(
                {"_id": ObjectId(request.project_id)},
                {"$set": {"storyboard_id": str(result.inserted_id), "updated_at": now}}
            )

        return self._serialize(created)

    async def get_by_id(self, storyboard_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(storyboard_id):
            return None
        doc = await self._collection().find_one({"_id": ObjectId(storyboard_id)})
        return self._serialize(doc) if doc else None

    async def get_by_project(self, project_id: str) -> Optional[dict]:
        doc = await self._collection().find_one({"project_id": project_id})
        return self._serialize(doc) if doc else None

    async def update_scene(
        self,
        storyboard_id: str,
        scene_number: int,
        updates: StoryboardSceneUpdate,
    ) -> Optional[dict]:
        """Update fields of an individual scene inside the storyboard."""
        storyboard = await self.get_by_id(storyboard_id)
        if not storyboard:
            return None

        scenes = storyboard.get("scenes", [])
        target_idx = None
        for i, s in enumerate(scenes):
            if s.get("scene_number") == scene_number:
                target_idx = i
                break

        if target_idx is None:
            return None

        # Apply non-null updates
        scene = scenes[target_idx]
        for field, value in updates.model_dump(exclude_unset=True).items():
            if value is not None:
                scene[field] = value

        scenes[target_idx] = scene
        now = datetime.now(timezone.utc)
        await self._collection().update_one(
            {"_id": ObjectId(storyboard_id)},
            {"$set": {"scenes": scenes, "updated_at": now}},
        )
        return await self.get_by_id(storyboard_id)

    async def regenerate_scene_prompt(
        self,
        storyboard_id: str,
        scene_number: int,
        additional_guidance: Optional[str] = None,
    ) -> Optional[dict]:
        """Use Gemini to rewrite the generative prompt of a specific scene."""
        storyboard = await self.get_by_id(storyboard_id)
        if not storyboard:
            return None

        scenes = storyboard.get("scenes", [])
        target_scene = None
        target_idx = None
        for i, s in enumerate(scenes):
            if s.get("scene_number") == scene_number:
                target_scene = s
                target_idx = i
                break

        if not target_scene:
            return None

        gemini = GeminiService()
        updated_data = await gemini.regenerate_scene_prompt(
            scene_data=target_scene,
            characters=storyboard.get("characters", []),
            visual_theme=storyboard.get("visual_theme", ""),
            additional_guidance=additional_guidance,
        )

        # Merge updated fields
        target_scene.update(updated_data)
        scenes[target_idx] = target_scene

        now = datetime.now(timezone.utc)
        await self._collection().update_one(
            {"_id": ObjectId(storyboard_id)},
            {"$set": {"scenes": scenes, "updated_at": now}},
        )
        return await self.get_by_id(storyboard_id)
