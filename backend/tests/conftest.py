import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock

from src.database.session import Base
from src.database.models import User, Document, DocumentVersion
from src.main import app
from src.config import settings
from src.core.auth import AuthenticatedUser


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine):
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_user(test_session):
    user = User(
        clerk_id="test_clerk_id",
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def client(test_user, test_session):
    from fastapi import Request
    from src.core.auth import get_current_user
    from src.database.session import get_db_session
    
    async def override_get_current_user(request: Request):
        return AuthenticatedUser(id=test_user.id, email=test_user.email, clerk_id=test_user.clerk_id)
    
    async def override_get_db_session():
        yield test_session
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth_headers(test_user):
    return {
        "Authorization": f"Bearer test_token_{test_user.id}",
        "X-User-Id": str(test_user.id),
        "X-User-Email": test_user.email,
    }
