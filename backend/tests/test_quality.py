import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from app.main import app
from app.routers.quality import (
    get_validator_service,
    get_visual_check_service,
    get_cost_service,
    get_version_service,
)
from app.models.quality import ValidationResult, VisualQualityCheck, CostEstimate


MOCK_VALIDATION = ValidationResult(
    file_exists=True,
    is_valid=True,
    format_name="MP4 / QuickTime",
    duration_seconds=15.0,
    file_size_bytes=1048576,
    video_codec="h264",
    resolution="1920x1080",
    fps=30.0,
    has_audio=True,
    audio_codec="aac",
    issues=[],
)

MOCK_VISUAL_CHECK = VisualQualityCheck(
    overall_aesthetic_score=9.0,
    character_consistency_score=9.2,
    cinematography_score=8.8,
    detected_flaws=[],
    optimization_recommendations=["Lighting continuity is consistent."],
    scene_evaluations=[{"scene_number": 1, "score": 9.0, "critique": "Crisp composition."}],
)

MOCK_COST = CostEstimate(
    project_id="proj_123",
    gemini_tokens=850,
    gemini_cost_usd=0.0025,
    tts_characters=450,
    tts_cost_usd=0.0,
    video_seconds=15.0,
    video_cost_usd=0.0,
    total_estimated_cost_usd=0.0025,
    cost_saving_recommendations=["Edge-TTS provides studio-grade voiceover at zero cost."],
)

MOCK_VERSION = {
    "_id": str(ObjectId()),
    "project_id": "proj_123",
    "version_number": 1,
    "label": "Initial Master Render",
    "video_path": "proj_123/output/final_video.mp4",
    "video_url": "/api/v1/files/proj_123/download/proj_123/output/final_video.mp4",
    "duration_seconds": 15.0,
    "file_size_bytes": 1048576,
    "is_active": True,
    "metadata": {},
    "created_at": "2026-11-07T18:00:00Z",
    "updated_at": "2026-11-07T18:00:00Z",
}


@pytest.mark.asyncio
async def test_validate_video(client):
    mock_service = MagicMock()
    mock_service.validate_project_output.return_value = MOCK_VALIDATION

    app.dependency_overrides[get_validator_service] = lambda: mock_service
    try:
        resp = await client.get("/api/v1/quality/validate/proj_123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True
        assert data["video_codec"] == "h264"
        assert data["resolution"] == "1920x1080"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_visual_audit(client):
    mock_service = AsyncMock()
    mock_service.audit_storyboard.return_value = MOCK_VISUAL_CHECK

    app.dependency_overrides[get_visual_check_service] = lambda: mock_service
    try:
        resp = await client.post(f"/api/v1/quality/visual-audit/{str(ObjectId())}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_aesthetic_score"] == 9.0
        assert data["character_consistency_score"] == 9.2
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cost_estimate(client):
    mock_service = AsyncMock()
    mock_service.calculate_project_cost.return_value = MOCK_COST

    app.dependency_overrides[get_cost_service] = lambda: mock_service
    try:
        resp = await client.get("/api/v1/quality/cost-estimate/proj_123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_estimated_cost_usd"] == 0.0025
        assert len(data["cost_saving_recommendations"]) > 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_versions(client):
    mock_service = AsyncMock()
    mock_service.list_versions.return_value = [MOCK_VERSION]

    app.dependency_overrides[get_version_service] = lambda: mock_service
    try:
        resp = await client.get("/api/v1/quality/versions/proj_123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_versions"] == 1
        assert data["versions"][0]["version_number"] == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_activate_version(client):
    mock_service = AsyncMock()
    mock_service.activate_version.return_value = MOCK_VERSION

    app.dependency_overrides[get_version_service] = lambda: mock_service
    try:
        resp = await client.post("/api/v1/quality/versions/proj_123/activate/1")
        assert resp.status_code == 200
        assert resp.json()["version_number"] == 1
        assert resp.json()["is_active"] is True
    finally:
        app.dependency_overrides.clear()
