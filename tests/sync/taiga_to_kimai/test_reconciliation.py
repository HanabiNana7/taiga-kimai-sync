from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from taiga_kimai_sync.db.base import Base
from taiga_kimai_sync.db.models import (
    EpicMapping,
    ProjectMapping,
    TaskMapping,
)
from taiga_kimai_sync.kimai.models import (
    KimaiActivity,
    KimaiCustomer,
    KimaiProject,
)
from taiga_kimai_sync.sync.taiga_to_kimai.reconciliation import reconcile
from taiga_kimai_sync.taiga.models import (
    TaigaEpic,
    TaigaProject,
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


def make_project() -> TaigaProject:
    return TaigaProject(
        id=12,
        name="AI Department",
        slug="ai-department",
    )


def make_epic() -> TaigaEpic:
    return TaigaEpic(
        id=25,
        ref=10,
        subject="LLM System",
        project=12,
    )


def make_story() -> TaigaUserStory:
    return TaigaUserStory(
        id=50,
        ref=20,
        subject="RAG Architecture",
        project=12,
        status=1,
        is_closed=False,
    )


def make_task() -> TaigaTask:
    return TaigaTask(
        id=100,
        ref=30,
        subject="Install Vector Database",
        project=12,
        user_story=50,
        status=1,
        is_closed=False,
    )


def make_kimai() -> SimpleNamespace:
    return SimpleNamespace(
        customers=SimpleNamespace(
            get=AsyncMock(),
            update=AsyncMock(),
        ),
        projects=SimpleNamespace(
            get=AsyncMock(),
            update=AsyncMock(),
        ),
        activities=SimpleNamespace(
            get=AsyncMock(),
            update=AsyncMock(),
        ),
    )


@pytest.mark.asyncio
async def test_reconcile_syncs_full_hierarchy(
    session: AsyncSession,
) -> None:
    taiga_project = make_project()
    taiga_epic = make_epic()
    taiga_story = make_story()
    taiga_task = make_task()

    taiga = SimpleNamespace(
        get_projects=AsyncMock(
            return_value=[taiga_project],
        ),
        get_epics=AsyncMock(
            return_value=[taiga_epic],
        ),
        get_user_stories=AsyncMock(
            return_value=[taiga_story],
        ),
        get_tasks=AsyncMock(
            return_value=[taiga_task],
        ),
    )

    kimai = make_kimai()

    with (
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_customer",
            new_callable=AsyncMock,
        ) as sync_customer,
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_project",
            new_callable=AsyncMock,
        ) as sync_project,
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_activity",
            new_callable=AsyncMock,
        ) as sync_activity,
    ):
        await reconcile(
            taiga=taiga,
            kimai=kimai,
            session=session,
        )

    taiga.get_projects.assert_awaited_once_with()

    taiga.get_epics.assert_awaited_once_with(
        project_id=12,
    )

    taiga.get_user_stories.assert_awaited_once_with(
        epic_id=25,
    )

    taiga.get_tasks.assert_awaited_once_with(
        user_story_id=50,
    )

    sync_customer.assert_awaited_once_with(
        taiga_project=taiga_project,
        kimai=kimai,
        session=session,
    )

    sync_project.assert_awaited_once_with(
        taiga_epic=taiga_epic,
        kimai=kimai,
        session=session,
    )

    sync_activity.assert_awaited_once_with(
        taiga_task=taiga_task,
        taiga_story=taiga_story,
        taiga_epic=taiga_epic,
        kimai=kimai,
        session=session,
    )


@pytest.mark.asyncio
async def test_reconcile_does_nothing_when_no_projects(
    session: AsyncSession,
) -> None:
    taiga = SimpleNamespace(
        get_projects=AsyncMock(
            return_value=[],
        ),
        get_epics=AsyncMock(),
        get_user_stories=AsyncMock(),
        get_tasks=AsyncMock(),
    )

    kimai = make_kimai()

    with (
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_customer",
            new_callable=AsyncMock,
        ) as sync_customer,
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_project",
            new_callable=AsyncMock,
        ) as sync_project,
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_activity",
            new_callable=AsyncMock,
        ) as sync_activity,
    ):
        await reconcile(
            taiga=taiga,
            kimai=kimai,
            session=session,
        )

    taiga.get_projects.assert_awaited_once_with()

    taiga.get_epics.assert_not_awaited()
    taiga.get_user_stories.assert_not_awaited()
    taiga.get_tasks.assert_not_awaited()

    sync_customer.assert_not_awaited()
    sync_project.assert_not_awaited()
    sync_activity.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_task_hides_activity(
    session: AsyncSession,
) -> None:
    session.add(
        TaskMapping(
            taiga_task_id=100,
            kimai_activity_id=501,
        )
    )
    await session.commit()

    activity = KimaiActivity(
        id=501,
        name="[RAG Architecture] Install Vector Database",
        project=81,
        visible=True,
    )

    kimai = make_kimai()
    kimai.activities.get.return_value = activity

    taiga = SimpleNamespace(
        get_projects=AsyncMock(
            return_value=[make_project()],
        ),
        get_epics=AsyncMock(
            return_value=[make_epic()],
        ),
        get_user_stories=AsyncMock(
            return_value=[make_story()],
        ),
        get_tasks=AsyncMock(
            return_value=[],
        ),
    )

    with (
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_customer",
            new_callable=AsyncMock,
        ),
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_project",
            new_callable=AsyncMock,
        ),
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_activity",
            new_callable=AsyncMock,
        ),
    ):
        await reconcile(
            taiga=taiga,
            kimai=kimai,
            session=session,
        )

    kimai.activities.get.assert_awaited_once_with(501)
    kimai.activities.update.assert_awaited_once()

    kimai.projects.update.assert_not_awaited()
    kimai.customers.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_epic_hides_project(
    session: AsyncSession,
) -> None:
    session.add(
        EpicMapping(
            taiga_epic_id=25,
            kimai_project_id=81,
        )
    )
    await session.commit()

    project = KimaiProject(
        id=81,
        name="LLM System",
        customer=37,
        visible=True,
    )

    kimai = make_kimai()
    kimai.projects.get.return_value = project

    taiga = SimpleNamespace(
        get_projects=AsyncMock(
            return_value=[make_project()],
        ),
        get_epics=AsyncMock(
            return_value=[],
        ),
        get_user_stories=AsyncMock(),
        get_tasks=AsyncMock(),
    )

    with (
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_customer",
            new_callable=AsyncMock,
        ),
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_project",
            new_callable=AsyncMock,
        ),
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_activity",
            new_callable=AsyncMock,
        ),
    ):
        await reconcile(
            taiga=taiga,
            kimai=kimai,
            session=session,
        )

    kimai.projects.get.assert_awaited_once_with(81)
    kimai.projects.update.assert_awaited_once()

    kimai.activities.update.assert_not_awaited()
    kimai.customers.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_project_hides_customer(
    session: AsyncSession,
) -> None:
    session.add(
        ProjectMapping(
            taiga_project_id=12,
            kimai_customer_id=37,
        )
    )
    await session.commit()

    customer = KimaiCustomer(
        id=37,
        name="AI Department",
        visible=True,
    )

    kimai = make_kimai()
    kimai.customers.get.return_value = customer

    taiga = SimpleNamespace(
        get_projects=AsyncMock(
            return_value=[],
        ),
        get_epics=AsyncMock(),
        get_user_stories=AsyncMock(),
        get_tasks=AsyncMock(),
    )

    with (
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_customer",
            new_callable=AsyncMock,
        ),
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_project",
            new_callable=AsyncMock,
        ),
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_activity",
            new_callable=AsyncMock,
        ),
    ):
        await reconcile(
            taiga=taiga,
            kimai=kimai,
            session=session,
        )

    kimai.customers.get.assert_awaited_once_with(37)
    kimai.customers.update.assert_awaited_once()

    kimai.activities.update.assert_not_awaited()
    kimai.projects.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_api_failure_does_not_run_missing_cleanup(
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
            TaskMapping(
                taiga_task_id=100,
                kimai_activity_id=501,
            ),
        ]
    )
    await session.commit()

    taiga = SimpleNamespace(
        get_projects=AsyncMock(
            return_value=[make_project()],
        ),
        get_epics=AsyncMock(
            side_effect=RuntimeError("Taiga API failed"),
        ),
        get_user_stories=AsyncMock(),
        get_tasks=AsyncMock(),
    )

    kimai = make_kimai()

    with (
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_customer",
            new_callable=AsyncMock,
        ),
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_project",
            new_callable=AsyncMock,
        ),
        patch(
            "taiga_kimai_sync.sync.taiga_to_kimai.reconciliation.sync_activity",
            new_callable=AsyncMock,
        ),
        pytest.raises(
            RuntimeError,
            match="Taiga API failed",
        ),
    ):
        await reconcile(
            taiga=taiga,
            kimai=kimai,
            session=session,
        )

    kimai.activities.get.assert_not_awaited()
    kimai.activities.update.assert_not_awaited()

    kimai.projects.get.assert_not_awaited()
    kimai.projects.update.assert_not_awaited()

    kimai.customers.get.assert_not_awaited()
    kimai.customers.update.assert_not_awaited()
