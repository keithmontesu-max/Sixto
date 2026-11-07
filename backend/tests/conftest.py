"""Pytest fixtures — in-memory SQLite for speed (no Postgres needed in CI)."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app as fastapi_app
from app.database import Base, get_db
from app import models  # noqa: F401

TEST_DB = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DB)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def override_db():
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    fastapi_app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()
