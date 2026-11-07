from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from app.database import get_db
from app.models.project import Project, ProjectCreate, ProjectUpdate, ProjectStatus


class ProjectService:
    """CRUD operations for Project documents."""

    def _collection(self):
        return get_db()["projects"]

    def _serialize(self, doc: dict) -> dict:
        """Convert MongoDB doc to serializable dict."""
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def create(self, data: ProjectCreate) -> dict:
        doc = {
            **data.model_dump(),
            "status": ProjectStatus.DRAFT,
            "script_id": None,
            "storyboard_id": None,
            "output_video_url": None,
            "thumbnail_url": None,
            "duration_actual": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = await self._collection().insert_one(doc)
        created = await self._collection().find_one({"_id": result.inserted_id})
        return self._serialize(created)

    async def get_by_id(self, project_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(project_id):
            return None
        doc = await self._collection().find_one({"_id": ObjectId(project_id)})
        return self._serialize(doc) if doc else None

    async def list_all(self, skip: int = 0, limit: int = 20) -> List[dict]:
        cursor = self._collection().find().sort("created_at", -1).skip(skip).limit(limit)
        return [self._serialize(doc) async for doc in cursor]

    async def update(self, project_id: str, data: ProjectUpdate) -> Optional[dict]:
        if not ObjectId.is_valid(project_id):
            return None
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        await self._collection().update_one(
            {"_id": ObjectId(project_id)},
            {"$set": update_data},
        )
        return await self.get_by_id(project_id)

    async def delete(self, project_id: str) -> bool:
        if not ObjectId.is_valid(project_id):
            return False
        result = await self._collection().delete_one({"_id": ObjectId(project_id)})
        return result.deleted_count > 0

    async def update_status(self, project_id: str, status: ProjectStatus) -> None:
        if not ObjectId.is_valid(project_id):
            return
        await self._collection().update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}},
        )

