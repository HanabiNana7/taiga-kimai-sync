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
from taiga_kimai_sync.db.models import EpicMapping, TaskMapping
from taiga_kimai_sync.kimai.models import KimaiActivity
from taiga_kimai_sync.sync.taiga_to_kimai.activities import sync_activity
from taiga_kimai_sync.taiga.models import (
    TaigaEpic,
    TaigaTask,
    TaigaUserStory,
)


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


def make_epic() -> TaigaEpic:
    return TaigaEpic(
        id=25,
        ref=10,
        subject="LLM System",
        project=12,
    )


def make_story(
    *,
    subject: str = "RAG Architecture",
    project: int = 12,
) -> TaigaUserStory:
    return TaigaUserStory(
        id=50,
        ref=20,
        subject=subject,
        project=project,
        status=1,
        is_closed=False,
    )


def make_task(
    *,
    subject: str = "Install Vector Database",
    user_story: int | None = 50,
    is_closed: bool = False,
) -> TaigaTask:
    return TaigaTask(
        id=100,
        ref=30,
        subject=subject,
        project=12,
        user_story=user_story,
        status=1,
        is_closed=is_closed,
    )


def make_kimai(
    *,
    get: AsyncMock | None = None,
    create: AsyncMock | None = None,
    update: AsyncMock | None = None,
) -> SimpleNamespace:
    activities = SimpleNamespace(
        get=get or AsyncMock(),
        create=create or AsyncMock(),
        update=update or AsyncMock(),
    )

    return SimpleNamespace(activities=activities)


@pytest.mark.asyncio
async def test_missing_epic_mapping_raises_error(
    session: AsyncSession,
) -> None:
    kimai = make_kimai()

    with pytest.raises(
        RuntimeError,
        match="Epic mapping not found for Taiga epic 25",
    ):
        await sync_activity(
            taiga_task=make_task(),
            taiga_story=make_story(),
            taiga_epic=make_epic(),
            kimai=kimai,
            session=session,
        )

    kimai.activities.get.assert_not_awaited()
    kimai.activities.create.assert_not_awaited()
    kimai.activities.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_task_story_relationship_mismatch_raises_error(
    session: AsyncSession,
) -> None:
    kimai = make_kimai()

    with pytest.raises(
        RuntimeError,
        match="Taiga task 100 does not belong to user story 50",
    ):
        await sync_activity(
            taiga_task=make_task(user_story=999),
            taiga_story=make_story(),
            taiga_epic=make_epic(),
            kimai=kimai,
            session=session,
        )

    kimai.activities.get.assert_not_awaited()
    kimai.activities.create.assert_not_awaited()
    kimai.activities.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_activity_and_mapping(
    session: AsyncSession,
) -> None:
    session.add(
        EpicMapping(
            taiga_epic_id=25,
            kimai_project_id=81,
        )
    )
    await session.commit()

    created_activity = KimaiActivity(
        id=501,
        name="[RAG Architecture] Install Vector Database",
        project=81,
        visible=True,
    )

    kimai = make_kimai(
        create=AsyncMock(return_value=created_activity),
    )

    result = await sync_activity(
        taiga_task=make_task(),
        taiga_story=make_story(),
        taiga_epic=make_epic(),
        kimai=kimai,
        session=session,
    )

    assert result == created_activity

    kimai.activities.create.assert_awaited_once()
    kimai.activities.get.assert_not_awaited()
    kimai.activities.update.assert_not_awaited()

    statement = select(TaskMapping).where(
        TaskMapping.taiga_task_id == 100,
    )

    mapping = (await session.execute(statement)).scalar_one()

    assert mapping.taiga_task_id == 100
    assert mapping.kimai_activity_id == 501


@pytest.mark.asyncio
async def test_existing_activity_is_not_updated(
    session: AsyncSession,
) -> None:
    session.add_all(
        [
            EpicMapping(
                taiga_epic_id=25,
                kimai_project_id=81,
            ),
            TaskMapping(
                taiga_task_id=100,
                kimai_activity_id=501,
            ),
        ]
    )
    await session.commit()

    existing_activity = KimaiActivity(
        id=501,
        name="[RAG Architecture] Install Vector Database",
        project=81,
        visible=True,
    )

    kimai = make_kimai(
        get=AsyncMock(return_value=existing_activity),
    )

    result = await sync_activity(
        taiga_task=make_task(),
        taiga_story=make_story(),
        taiga_epic=make_epic(),
        kimai=kimai,
        session=session,
    )

    assert result == existing_activity

    kimai.activities.get.assert_awaited_once_with(501)
    kimai.activities.create.assert_not_awaited()
    kimai.activities.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_activity_name_is_updated(
    session: AsyncSession,
) -> None:
    session.add_all(
        [
            EpicMapping(
                taiga_epic_id=25,
                kimai_project_id=81,
            ),
            TaskMapping(
                taiga_task_id=100,
                kimai_activity_id=501,
            ),
        ]
    )
    await session.commit()

    existing_activity = KimaiActivity(
        id=501,
        name="[RAG Architecture] Install Vector Database",
        project=81,
        visible=True,
    )

    updated_activity = KimaiActivity(
        id=501,
        name="[RAG Core Architecture] Install Vector Database",
        project=81,
        visible=True,
    )

    kimai = make_kimai(
        get=AsyncMock(return_value=existing_activity),
        update=AsyncMock(return_value=updated_activity),
    )

    result = await sync_activity(
        taiga_task=make_task(),
        taiga_story=make_story(
            subject="RAG Core Architecture",
        ),
        taiga_epic=make_epic(),
        kimai=kimai,
        session=session,
    )

    assert result == updated_activity
    assert result.id == 501

    kimai.activities.create.assert_not_awaited()
    kimai.activities.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_activity_project_is_updated(
    session: AsyncSession,
) -> None:
    session.add_all(
        [
            EpicMapping(
                taiga_epic_id=25,
                kimai_project_id=90,
            ),
            TaskMapping(
                taiga_task_id=100,
                kimai_activity_id=501,
            ),
        ]
    )
    await session.commit()

    existing_activity = KimaiActivity(
        id=501,
        name="[RAG Architecture] Install Vector Database",
        project=81,
        visible=True,
    )

    updated_activity = KimaiActivity(
        id=501,
        name="[RAG Architecture] Install Vector Database",
        project=90,
        visible=True,
    )

    kimai = make_kimai(
        get=AsyncMock(return_value=existing_activity),
        update=AsyncMock(return_value=updated_activity),
    )

    result = await sync_activity(
        taiga_task=make_task(),
        taiga_story=make_story(),
        taiga_epic=make_epic(),
        kimai=kimai,
        session=session,
    )

    assert result.project == 90

    kimai.activities.create.assert_not_awaited()
    kimai.activities.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_closed_task_hides_activity(
    session: AsyncSession,
) -> None:
    session.add_all(
        [
            EpicMapping(
                taiga_epic_id=25,
                kimai_project_id=81,
            ),
            TaskMapping(
                taiga_task_id=100,
                kimai_activity_id=501,
            ),
        ]
    )
    await session.commit()

    existing_activity = KimaiActivity(
        id=501,
        name="[RAG Architecture] Install Vector Database",
        project=81,
        visible=True,
    )

    hidden_activity = KimaiActivity(
        id=501,
        name="[RAG Architecture] Install Vector Database",
        project=81,
        visible=False,
    )

    kimai = make_kimai(
        get=AsyncMock(return_value=existing_activity),
        update=AsyncMock(return_value=hidden_activity),
    )

    result = await sync_activity(
        taiga_task=make_task(is_closed=True),
        taiga_story=make_story(),
        taiga_epic=make_epic(),
        kimai=kimai,
        session=session,
    )

    assert result.visible is False

    kimai.activities.create.assert_not_awaited()
    kimai.activities.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_reopened_task_shows_activity(
    session: AsyncSession,
) -> None:
    session.add_all(
        [
            EpicMapping(
                taiga_epic_id=25,
                kimai_project_id=81,
            ),
            TaskMapping(
                taiga_task_id=100,
                kimai_activity_id=501,
            ),
        ]
    )
    await session.commit()

    hidden_activity = KimaiActivity(
        id=501,
        name="[RAG Architecture] Install Vector Database",
        project=81,
        visible=False,
    )

    visible_activity = KimaiActivity(
        id=501,
        name="[RAG Architecture] Install Vector Database",
        project=81,
        visible=True,
    )

    kimai = make_kimai(
        get=AsyncMock(return_value=hidden_activity),
        update=AsyncMock(return_value=visible_activity),
    )

    result = await sync_activity(
        taiga_task=make_task(is_closed=False),
        taiga_story=make_story(),
        taiga_epic=make_epic(),
        kimai=kimai,
        session=session,
    )

    assert result.visible is True

    kimai.activities.create.assert_not_awaited()
    kimai.activities.update.assert_awaited_once()
