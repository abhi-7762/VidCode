import pytest
from unittest.mock import AsyncMock
from bson import ObjectId
from app.main import app
from app.routers.videos import get_video_service


MOCK_CLIP = {
    "_id": str(ObjectId()),
    "project_id": "proj_123",
    "storyboard_id": str(ObjectId()),
    "scene_number": 1,
    "provider": "mock",
    "external_task_id": "mock_task_abc",
    "status": "completed",
    "progress": 100,
    "prompt_used": "Cinematic shot of futuristic cityscape",
    "video_url": "https://mock-storage.vidcode.ai/clips/mock_task_abc.mp4",
    "local_file_path": "proj_123/clips/scene_1.mp4",
    "duration_seconds": 5.0,
    "file_size_bytes": 10240,
    "error_message": None,
    "retry_count": 0,
    "created_at": "2026-11-07T18:00:00Z",
    "updated_at": "2026-11-07T18:00:00Z",
}


@pytest.mark.asyncio
async def test_generate_clips(client):
    mock_service = AsyncMock()
    mock_service.generate_clips_for_storyboard.return_value = [MOCK_CLIP]

    app.dependency_overrides[get_video_service] = lambda: mock_service
    try:
        resp = await client.post("/api/v1/videos/generate", json={
            "project_id": "proj_123",
            "storyboard_id": str(ObjectId()),
            "provider": "mock",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_clips"] == 1
        assert data["clips"][0]["provider"] == "mock"
        assert data["clips"][0]["status"] == "completed"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_project_clips(client):
    mock_service = AsyncMock()
    mock_service.get_clips_by_project.return_value = [MOCK_CLIP]

    app.dependency_overrides[get_video_service] = lambda: mock_service
    try:
        resp = await client.get("/api/v1/videos/project/proj_123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_clips"] == 1
        assert data["clips"][0]["_id"] == MOCK_CLIP["_id"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_clip_by_id(client):
    mock_service = AsyncMock()
    mock_service.get_clip_by_id.return_value = MOCK_CLIP

    app.dependency_overrides[get_video_service] = lambda: mock_service
    try:
        resp = await client.get(f"/api/v1/videos/clips/{MOCK_CLIP['_id']}")
        assert resp.status_code == 200
        assert resp.json()["_id"] == MOCK_CLIP["_id"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_regenerate_clip(client):
    updated_clip = dict(MOCK_CLIP)
    updated_clip["retry_count"] = 1
    mock_service = AsyncMock()
    mock_service.regenerate_clip.return_value = updated_clip

    app.dependency_overrides[get_video_service] = lambda: mock_service
    try:
        resp = await client.post(
            f"/api/v1/videos/clips/{MOCK_CLIP['_id']}/regenerate",
            json={"prompt_override": "Updated shot description"}
        )
        assert resp.status_code == 200
        assert resp.json()["retry_count"] == 1
    finally:
        app.dependency_overrides.clear()

