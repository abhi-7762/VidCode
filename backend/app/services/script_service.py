"""
Script Service — orchestrates Gemini + MongoDB for script lifecycle.
"""
from datetime import datetime
from typing import Optional
from bson import ObjectId

from app.database import get_db
from app.services.gemini_service import GeminiService
from app.models.script import Script, ScriptGenerateRequest, ScriptScene


class ScriptService:
    """Manages script generation and storage."""

    def _collection(self):
        return get_db()["scripts"]

    def _serialize(self, doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def generate(self, request: ScriptGenerateRequest) -> dict:
        """
        Full pipeline:
          1. NLU — understand the prompt
          2. Generate script via Gemini
          3. Save to MongoDB
          4. Return serialized doc
        """
        gemini = GeminiService()

        # Step 1: NLU
        nlu = await gemini.analyse_prompt(request.prompt, request.duration_seconds)

        # Step 2: Script generation
        script_data = await gemini.generate_script(request, nlu)

        # Step 3: Persist
        doc = {
            "project_id": request.project_id,
            "raw_prompt": request.prompt,
            "nlu_analysis": nlu.model_dump(),
            "gemini_model": "gemini-1.5-pro",
            "generation_tokens": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **script_data,
        }
        result = await self._collection().insert_one(doc)
        created = await self._collection().find_one({"_id": result.inserted_id})
        return self._serialize(created)

    async def get_by_id(self, script_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(script_id):
            return None
        doc = await self._collection().find_one({"_id": ObjectId(script_id)})
        return self._serialize(doc) if doc else None

    async def get_by_project(self, project_id: str) -> Optional[dict]:
        doc = await self._collection().find_one({"project_id": project_id})
        return self._serialize(doc) if doc else None

    async def improve(self, script_id: str, feedback: str) -> Optional[dict]:
        """Rewrite script with Gemini based on feedback."""
        script = await self.get_by_id(script_id)
        if not script:
            return None

        gemini = GeminiService()
        improved = await gemini.improve_script(script, feedback)

        improved["updated_at"] = datetime.utcnow()
        await self._collection().update_one(
            {"_id": ObjectId(script_id)},
            {"$set": improved},
        )
        return await self.get_by_id(script_id)

