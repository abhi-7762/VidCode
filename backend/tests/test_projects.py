import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId
from datetime import datetime


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


def make_client(mock_service):
    with patch("app.database.connect_db", new_callable=AsyncMock), \
         patch("app.database.close_db", new_callable=AsyncMock), \
         patch("app.routers.projects.ProjectService", return_value=mock_service):
        from app.main import app
        import importlib
        import app.main as main_mod
        importlib.reload(main_mod)
        return AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        )


@pytest.mark.asyncio
async def test_create_project():
    mock_service = AsyncMock()
    mock_service.create.return_value = MOCK_PROJECT

    with patch("app.database.connect_db", new_callable=AsyncMock), \
         patch("app.database.close_db", new_callable=AsyncMock), \
         patch("app.routers.projects.get_project_service", return_value=lambda: mock_service):
        from app.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/api/v1/projects/", json={
                "title": "Test Video",
                "prompt": "Create a 60-second explainer video about machine learning",
            })
        assert resp.status_code == 201


@pytest.mark.asyncio
async def test_list_projects():
    mock_service = AsyncMock()
    mock_service.list_all.return_value = [MOCK_PROJECT]

    with patch("app.database.connect_db", new_callable=AsyncMock), \
         patch("app.database.close_db", new_callable=AsyncMock), \
         patch("app.routers.projects.get_project_service", return_value=lambda: mock_service):
        from app.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/v1/projects/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

