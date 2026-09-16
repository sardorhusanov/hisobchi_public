from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.api.dependencies.auth import TelegramIdentity, get_identity
from app.db.session import Session
from app.repositories.core import Repository
from app.services.core import WorkspaceService


async def get_current_workspace(
    identity: Annotated[TelegramIdentity, Depends(get_identity)],
) -> AsyncIterator[Repository]:
    async with Session() as session:
        async with session.begin():
            workspace = await WorkspaceService(session).initialize(identity.id, identity.first_name)
            yield Repository(session, workspace.id)


# Function scope commits BEFORE FastAPI sends the response.
CurrentRepository = Annotated[Repository, Depends(get_current_workspace, scope="function")]
