import os
from collections.abc import AsyncGenerator

os.environ["TESTING"] = "1"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.db.session import get_db

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/blog_db_test"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    AsyncSessionTest = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncSessionTest() as session:
        yield session


@pytest.fixture(autouse=True)
def mock_storage(monkeypatch):
    def fake_upload(file_obj, filename: str, content_type: str | None = None) -> str:
        return f"http://test.local/fake/{filename}"

    import app.services.storage

    monkeypatch.setattr(app.services.storage, "upload_image_file", fake_upload)


@pytest.fixture(autouse=True)
def mock_celery(monkeypatch):
    def fake_delay(*args, **kwargs):
        pass

    import app.tasks.email_tasks

    monkeypatch.setattr(
        app.tasks.email_tasks.send_registration_email_task, "delay", fake_delay
    )


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
