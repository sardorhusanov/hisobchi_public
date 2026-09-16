import os
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.repositories.core import Repository
from app.services.core import WorkspaceService


@pytest_asyncio.fixture
async def context():
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"])
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = async_sessionmaker(bind=connection, expire_on_commit=False)()
        workspace = await WorkspaceService(session).initialize(uuid4().int % (2**62), "Sardor")
        repo = Repository(session, workspace.id)
        yield session, repo
        await session.close()
        await transaction.rollback()
    await engine.dispose()
