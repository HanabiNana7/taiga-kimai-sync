from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from taiga_kimai_sync.db.base import Base
from taiga_kimai_sync.db.models import EpicMapping, ProjectMapping
from taiga_kimai_sync.kimai.models import KimaiProject
from taiga_kimai_sync.sync.taiga_to_kimai.projects import sync_project
from taiga_kimai_sync.taiga.models import TaigaEpic


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_missing_project_mapping_raises_error(
    session: AsyncSession,
) -> None:
    taiga_epic = TaigaEpic(
        id=25,
        ref=10,
        subject="LLM System",
        project=12,
    )

    projects = SimpleNamespace(
        get=AsyncMock(),
        create=AsyncMock(),
        update=AsyncMock(),
    )
    kimai = SimpleNamespace(projects=projects)

    with pytest.raises(
        RuntimeError,
        match="Project mapping not found for Taiga project 12",
    ):
        await sync_project(
            taiga_epic=taiga_epic,
            kimai=kimai,
            session=session,
        )

    projects.get.assert_not_awaited()
    projects.create.assert_not_awaited()
    projects.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_project_and_mapping(
    session: AsyncSession,
) -> None:
    project_mapping = ProjectMapping(
        taiga_project_id=12,
        kimai_customer_id=37,
    )
    session.add(project_mapping)
    await session.commit()

    taiga_epic = TaigaEpic(
        id=25,
        ref=10,
        subject="LLM System",
        project=12,
    )

    created_project = KimaiProject(
        id=81,
        name="LLM System",
        customer=37,
        visible=True,
    )

    projects = SimpleNamespace(
        get=AsyncMock(),
        create=AsyncMock(return_value=created_project),
        update=AsyncMock(),
    )
    kimai = SimpleNamespace(projects=projects)

    result = await sync_project(
        taiga_epic=taiga_epic,
        kimai=kimai,
        session=session,
    )

    assert result == created_project

    projects.create.assert_awaited_once()
    projects.get.assert_not_awaited()
    projects.update.assert_not_awaited()

    query = select(EpicMapping).where(
        EpicMapping.taiga_epic_id == taiga_epic.id,
    )
    mapping = (await session.execute(query)).scalar_one()

    assert mapping.taiga_epic_id == 25
    assert mapping.kimai_project_id == 81


@pytest.mark.asyncio
async def test_existing_project_is_not_updated(
    session: AsyncSession,
) -> None:
    session.add_all(
        [
            ProjectMapping(
                taiga_project_id=12,
                kimai_customer_id=37,
            ),
            EpicMapping(
                taiga_epic_id=25,
                kimai_project_id=81,
            ),
        ]
    )
    await session.commit()

    taiga_epic = TaigaEpic(
        id=25,
        ref=10,
        subject="LLM System",
        project=12,
    )

    existing_project = KimaiProject(
        id=81,
        name="LLM System",
        customer=37,
        visible=True,
    )

    projects = SimpleNamespace(
        get=AsyncMock(return_value=existing_project),
        create=AsyncMock(),
        update=AsyncMock(),
    )
    kimai = SimpleNamespace(projects=projects)

    result = await sync_project(
        taiga_epic=taiga_epic,
        kimai=kimai,
        session=session,
    )

    assert result == existing_project

    projects.get.assert_awaited_once_with(81)
    projects.create.assert_not_awaited()
    projects.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_project_name_is_updated(
    session: AsyncSession,
) -> None:
    session.add_all(
        [
            ProjectMapping(
                taiga_project_id=12,
                kimai_customer_id=37,
            ),
            EpicMapping(
                taiga_epic_id=25,
                kimai_project_id=81,
            ),
        ]
    )
    await session.commit()

    taiga_epic = TaigaEpic(
        id=25,
        ref=10,
        subject="LLM Platform",
        project=12,
    )

    existing_project = KimaiProject(
        id=81,
        name="LLM System",
        customer=37,
        visible=True,
    )

    updated_project = KimaiProject(
        id=81,
        name="LLM Platform",
        customer=37,
        visible=True,
    )

    projects = SimpleNamespace(
        get=AsyncMock(return_value=existing_project),
        create=AsyncMock(),
        update=AsyncMock(return_value=updated_project),
    )
    kimai = SimpleNamespace(projects=projects)

    result = await sync_project(
        taiga_epic=taiga_epic,
        kimai=kimai,
        session=session,
    )

    assert result == updated_project
    assert result.id == 81

    projects.create.assert_not_awaited()
    projects.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_project_customer_and_visibility_are_updated(
    session: AsyncSession,
) -> None:
    session.add_all(
        [
            ProjectMapping(
                taiga_project_id=12,
                kimai_customer_id=37,
            ),
            EpicMapping(
                taiga_epic_id=25,
                kimai_project_id=81,
            ),
        ]
    )
    await session.commit()

    taiga_epic = TaigaEpic(
        id=25,
        ref=10,
        subject="LLM System",
        project=12,
    )

    existing_project = KimaiProject(
        id=81,
        name="LLM System",
        customer=99,
        visible=False,
    )

    updated_project = KimaiProject(
        id=81,
        name="LLM System",
        customer=37,
        visible=True,
    )

    projects = SimpleNamespace(
        get=AsyncMock(return_value=existing_project),
        create=AsyncMock(),
        update=AsyncMock(return_value=updated_project),
    )
    kimai = SimpleNamespace(projects=projects)

    result = await sync_project(
        taiga_epic=taiga_epic,
        kimai=kimai,
        session=session,
    )

    assert result.customer == 37
    assert result.visible is True

    projects.create.assert_not_awaited()
    projects.update.assert_awaited_once()
