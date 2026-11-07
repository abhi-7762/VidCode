import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_root():
    with patch("app.database.connect_db", new_callable=AsyncMock), \
         patch("app.database.close_db", new_callable=AsyncMock):
        from app.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/")
        assert resp.status_code == 200
        assert resp.json()["app"] == "VidCode"


@pytest.mark.asyncio
async def test_health():
    with patch("app.database.connect_db", new_callable=AsyncMock), \
         patch("app.database.close_db", new_callable=AsyncMock):
        from app.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

