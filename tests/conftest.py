import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.main import app
from app.db import session as app_db_session

settings = get_settings()

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/blog_db_test"

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)
AsyncSessionTest = async_sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Отдаём общий event loop для pytest-asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    """Создаём схему в тестовой БД один раз за сессию."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionTest() as session:
        yield session


@pytest.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    from app.db import session as app_db_session

    app_db_session.get_db = _get_test_db  # type: ignore

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
