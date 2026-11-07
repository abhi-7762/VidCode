import pytest
from unittest.mock import AsyncMock
from bson import ObjectId
from datetime import datetime
from app.main import app
from app.routers.projects import get_project_service

MOCK_PROJECT = {
    "_id": str(ObjectId()),
    "title": "Test Video",
    "description": "A test project",
    "prompt": "Create a 60-second explainer video about machine learning",
    "status": "draft",
    "settings": {
        "duration_seconds": 60,
        "resolution": "1080p",
        "style": "cinematic",
        "voice_id": None,
        "background_music": True,
        "subtitles": True,
    },
    "tags": ["ml", "education"],
    "script_id": None,
    "storyboard_id": None,
    "output_video_url": None,
    "thumbnail_url": None,
    "duration_actual": None,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat(),
}


@pytest.mark.asyncio
async def test_create_project(client):
    mock_service = AsyncMock()
    mock_service.create.return_value = MOCK_PROJECT

    app.dependency_overrides[get_project_service] = lambda: mock_service
    try:
        resp = await client.post("/api/v1/projects/", json={
            "title": "Test Video",
            "prompt": "Create a 60-second explainer video about machine learning",
        })
        assert resp.status_code == 201
        assert resp.json()["title"] == "Test Video"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_projects(client):
    mock_service = AsyncMock()
    mock_service.list_all.return_value = [MOCK_PROJECT]

    app.dependency_overrides[get_project_service] = lambda: mock_service
    try:
        resp = await client.get("/api/v1/projects/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 1
    finally:
        app.dependency_overrides.clear()
