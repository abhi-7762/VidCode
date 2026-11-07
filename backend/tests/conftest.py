import os
os.environ["TESTING"] = "true"

import pytest
from httpx import AsyncClient, ASGITransport
from app.config import get_settings

get_settings.cache_clear()


@pytest.fixture
async def client():
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
