import pytest
from unittest.mock import AsyncMock, patch
from bson import ObjectId
from app.main import app
from app.routers.scripts import get_script_service


MOCK_SCRIPT = {
    "_id": str(ObjectId()),
    "project_id": "test_project_123",
    "raw_prompt": "Create an explainer on quantum computing",
    "title": "Quantum Leap Explained",
    "logline": "Discover how quantum bits revolutionize computers.",
    "hook": "What if your computer could calculate in seconds what takes millennia?",
    "call_to_action": "Subscribe to explore more computing breakthroughs.",
    "total_duration_seconds": 60,
    "word_count": 120,
    "scenes": [
        {
            "scene_number": 1,
            "title": "The Quantum Realm",
            "duration_seconds": 15,
            "narration": "In the classical world, bits are either zero or one.",
            "dialogue": None,
            "action": "Glowing digital binary numbers morph into multi-dimensional spheres.",
            "emotion": "Wonder",
            "transition": "fade",
        }
    ],
    "nlu_analysis": {
        "topic": "Quantum Computing",
        "genre": "educational",
        "tone": "educational",
        "style": "narration",
        "target_audience": "Tech enthusiasts",
        "key_messages": ["Qubits use superposition", "Exponential speedups"],
        "suggested_duration_seconds": 60,
        "visual_style": "cinematic neon cyberpunk",
        "mood": "futuristic",
        "language": "English",
        "confidence": 0.95,
    },
    "created_at": "2026-11-07T18:00:00Z",
}


@pytest.mark.asyncio
async def test_generate_script(client):
    mock_service = AsyncMock()
    mock_service.generate.return_value = MOCK_SCRIPT

    app.dependency_overrides[get_script_service] = lambda: mock_service
    try:
        resp = await client.post("/api/v1/scripts/generate", json={
            "project_id": "test_project_123",
            "prompt": "Create an explainer on quantum computing",
            "duration_seconds": 60,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Quantum Leap Explained"
        assert len(data["scenes"]) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_script_by_id(client):
    mock_service = AsyncMock()
    mock_service.get_by_id.return_value = MOCK_SCRIPT

    app.dependency_overrides[get_script_service] = lambda: mock_service
    try:
        resp = await client.get(f"/api/v1/scripts/{MOCK_SCRIPT['_id']}")
        assert resp.status_code == 200
        assert resp.json()["_id"] == MOCK_SCRIPT["_id"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_script_by_project(client):
    mock_service = AsyncMock()
    mock_service.get_by_project.return_value = MOCK_SCRIPT

    app.dependency_overrides[get_script_service] = lambda: mock_service
    try:
        resp = await client.get("/api/v1/scripts/project/test_project_123")
        assert resp.status_code == 200
        assert resp.json()["project_id"] == "test_project_123"
    finally:
        app.dependency_overrides.clear()

