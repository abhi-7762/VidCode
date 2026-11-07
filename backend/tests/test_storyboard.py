import pytest
from unittest.mock import AsyncMock
from bson import ObjectId
from app.main import app
from app.routers.storyboard import get_storyboard_service


MOCK_STORYBOARD = {
    "_id": str(ObjectId()),
    "project_id": "proj_123",
    "script_id": str(ObjectId()),
    "aspect_ratio": "16:9",
    "visual_theme": "cyberpunk noir, cinematic 8k",
    "characters": [
        {
            "name": "Dr. Sarah Vance",
            "appearance": "mid-30s woman, sharp jawline, short silver hair, cybernetic iris",
            "outfit": "charcoal high-collar trench coat with glowing cyan lining",
            "consistency_tags": ["short silver hair", "cybernetic iris", "charcoal trench coat"],
        }
    ],
    "scenes": [
        {
            "scene_number": 1,
            "title": "Laboratory of the Future",
            "duration_seconds": 6,
            "script_scene_number": 1,
            "action_description": "Dr. Vance operates a levitating holographic quantum processor.",
            "narration_cue": "In the classical world, bits are either zero or one.",
            "camera": {
                "shot_type": "medium_close_up",
                "camera_angle": "low_angle",
                "movement": "dolly_in",
                "lens": "35mm anamorphic",
                "depth_of_field": "shallow focus with anamorphic streak flares",
                "lighting": "moody dark room illuminated by cyan holographic light",
            },
            "characters_present": ["Dr. Sarah Vance"],
            "environment": "High-tech quantum laboratory, night, rain beating on towering glass windows",
            "visual_prompt": "Cinematic low-angle medium close-up of Dr. Sarah Vance with short silver hair and cybernetic iris, charcoal trench coat, operating a cyan holographic quantum sphere in a rainy dark high-tech lab, 8k photorealistic, anamorphic lens flares",
            "negative_prompt": "blurry, distorted, low quality, artifacts, text, watermark, deformed limbs",
            "motion_strength": 6,
            "transition_to_next": "cut",
        }
    ],
    "total_scenes": 1,
    "total_duration_seconds": 6,
    "created_at": "2026-11-07T18:00:00Z",
    "updated_at": "2026-11-07T18:00:00Z",
}


@pytest.mark.asyncio
async def test_generate_storyboard(client):
    mock_service = AsyncMock()
    mock_service.generate.return_value = MOCK_STORYBOARD

    app.dependency_overrides[get_storyboard_service] = lambda: mock_service
    try:
        resp = await client.post("/api/v1/storyboards/generate", json={
            "project_id": "proj_123",
            "script_id": str(ObjectId()),
            "aspect_ratio": "16:9",
            "visual_theme": "cyberpunk noir, cinematic 8k",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["visual_theme"] == "cyberpunk noir, cinematic 8k"
        assert len(data["characters"]) == 1
        assert data["characters"][0]["name"] == "Dr. Sarah Vance"
        assert len(data["scenes"]) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_storyboard_by_id(client):
    mock_service = AsyncMock()
    mock_service.get_by_id.return_value = MOCK_STORYBOARD

    app.dependency_overrides[get_storyboard_service] = lambda: mock_service
    try:
        resp = await client.get(f"/api/v1/storyboards/{MOCK_STORYBOARD['_id']}")
        assert resp.status_code == 200
        assert resp.json()["_id"] == MOCK_STORYBOARD["_id"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_scene(client):
    updated_sb = dict(MOCK_STORYBOARD)
    updated_sb["scenes"][0]["motion_strength"] = 8

    mock_service = AsyncMock()
    mock_service.update_scene.return_value = updated_sb

    app.dependency_overrides[get_storyboard_service] = lambda: mock_service
    try:
        resp = await client.patch(
            f"/api/v1/storyboards/{MOCK_STORYBOARD['_id']}/scenes/1",
            json={"motion_strength": 8}
        )
        assert resp.status_code == 200
        assert resp.json()["scenes"][0]["motion_strength"] == 8
    finally:
        app.dependency_overrides.clear()

