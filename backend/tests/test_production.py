import pytest
from unittest.mock import AsyncMock
from bson import ObjectId
from app.main import app
from app.routers.production import get_production_service, get_voice_service
from app.models.production import VoiceInfo, VoiceProviderType


MOCK_RENDER_JOB = {
    "_id": str(ObjectId()),
    "project_id": "proj_123",
    "storyboard_id": str(ObjectId()),
    "status": "completed",
    "progress": 100,
    "current_step": "Video render complete",
    "settings": {
        "voice_provider": "edge_tts",
        "voice_name": "en-US-ChristopherNeural",
        "include_voiceover": True,
        "include_subtitles": True,
        "subtitle_format": "srt",
        "background_music_enabled": False,
        "background_music_volume": 0.15,
        "voice_volume": 1.0,
        "resolution": "1080p",
        "fps": 30,
    },
    "output_video_path": "proj_123/output/final_video.mp4",
    "output_video_url": "/api/v1/files/proj_123/download/proj_123/output/final_video.mp4",
    "voiceover_path": "proj_123/voiceover.mp3",
    "subtitle_path": "proj_123/subtitles.srt",
    "duration_seconds": 15.0,
    "file_size_bytes": 1048576,
    "error_message": None,
    "created_at": "2026-11-07T18:00:00Z",
    "updated_at": "2026-11-07T18:00:00Z",
}


@pytest.mark.asyncio
async def test_list_voices(client):
    resp = await client.get("/api/v1/production/voices")
    assert resp.status_code == 200
    voices = resp.json()
    assert isinstance(voices, list)
    assert len(voices) > 0
    assert any(v["id"] == "en-US-ChristopherNeural" for v in voices)


@pytest.mark.asyncio
async def test_start_render(client):
    mock_service = AsyncMock()
    mock_service.create_render_job.return_value = MOCK_RENDER_JOB

    app.dependency_overrides[get_production_service] = lambda: mock_service
    try:
        resp = await client.post("/api/v1/production/render", json={
            "project_id": "proj_123",
            "storyboard_id": str(ObjectId()),
            "settings": {
                "voice_name": "en-US-ChristopherNeural",
                "include_voiceover": True,
                "include_subtitles": True,
                "resolution": "1080p",
            }
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert "final_video.mp4" in data["output_video_url"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_render_job(client):
    mock_service = AsyncMock()
    mock_service.get_job_by_id.return_value = MOCK_RENDER_JOB

    app.dependency_overrides[get_production_service] = lambda: mock_service
    try:
        resp = await client.get(f"/api/v1/production/jobs/{MOCK_RENDER_JOB['_id']}")
        assert resp.status_code == 200
        assert resp.json()["_id"] == MOCK_RENDER_JOB["_id"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_project_renders(client):
    mock_service = AsyncMock()
    mock_service.get_jobs_by_project.return_value = [MOCK_RENDER_JOB]

    app.dependency_overrides[get_production_service] = lambda: mock_service
    try:
        resp = await client.get("/api/v1/production/project/proj_123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_renders"] == 1
        assert data["renders"][0]["_id"] == MOCK_RENDER_JOB["_id"]
    finally:
        app.dependency_overrides.clear()
