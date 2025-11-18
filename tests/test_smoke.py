import pytest
from quart.testing import QuartClient

from app import create_app


@pytest.fixture(scope="module")
def client() -> QuartClient:
    app = create_app()
    return app.test_client()


@pytest.mark.asyncio
async def test_index_returns_html(client: QuartClient):
    response = await client.get("/")
    assert response.status_code == 200
    text = await response.get_data(as_text=True)
    assert "Нейромагия" in text

