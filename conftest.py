from contextlib import asynccontextmanager

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient
from main import app
from database import Base, get_session

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test_workflow.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

@asynccontextmanager
async def override_get_session():
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture(scope="session", autouse=True)
async def apply_migrations():
    """Apply migrations before tests."""
    alembic_cfg = Config("alembic_test.ini")
    command.upgrade(alembic_cfg, "head")
    yield
    command.downgrade(alembic_cfg, "base")

@pytest.fixture(scope="function")
async def async_client():
    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture(scope="function", autouse=True)
async def clear_database():
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())



