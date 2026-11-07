import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_db():
    """Mock MongoDB so tests don't need a real connection."""
    with patch("app.database.connect_db", new_callable=AsyncMock), \
         patch("app.database.close_db", new_callable=AsyncMock), \
         patch("app.database.get_db") as mock_get_db:
        mock_col = AsyncMock()
        mock_get_db.return_value = {"projects": mock_col}
        yield mock_get_db


@pytest.fixture
async def client(mock_db):
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

