
import pytest
import asyncio
import sys
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport 

from app.main import app
from app.config import AsyncSessionLocal
from app.deps import get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def override_get_db():
    async with AsyncSessionLocal() as session:
        yield session

@pytest.fixture
async def client(override_get_db):
    app.dependency_overrides[get_db] = lambda: override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
