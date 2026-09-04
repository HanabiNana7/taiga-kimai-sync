from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taiga_kimai_sync.db.models import (
    EpicMapping,
    ProjectMapping,
    TaskMapping,
)
from taiga_kimai_sync.kimai.client import KimaiClient
from taiga_kimai_sync.kimai.models import (
    KimaiActivityUpdate,
    KimaiCustomerUpdate,
    KimaiProjectUpdate,
)
from taiga_kimai_sync.sync.taiga_to_kimai.activities import sync_activity
from taiga_kimai_sync.sync.taiga_to_kimai.customers import sync_customer
from taiga_kimai_sync.sync.taiga_to_kimai.projects import sync_project
from taiga_kimai_sync.taiga.client import TaigaClient


async def reconcile(
    taiga: TaigaClient,
    kimai: KimaiClient,
    session: AsyncSession,
) -> None:
    seen_project_ids: set[int] = set()
    seen_epic_ids: set[int] = set()
    seen_task_ids: set[int] = set()

    taiga_projects = await taiga.get_projects()

    for taiga_project in taiga_projects:
        seen_project_ids.add(taiga_project.id)

        await sync_customer(
            taiga_project=taiga_project,
            kimai=kimai,
            session=session,
        )

        taiga_epics = await taiga.get_epics(
            project_id=taiga_project.id,
        )

        for taiga_epic in taiga_epics:
            seen_epic_ids.add(taiga_epic.id)

            await sync_project(
                taiga_epic=taiga_epic,
                kimai=kimai,
                session=session,
            )

            taiga_stories = await taiga.get_user_stories(
                epic_id=taiga_epic.id,
            )

            for taiga_story in taiga_stories:
                taiga_tasks = await taiga.get_tasks(
                    user_story_id=taiga_story.id,
                )

                for taiga_task in taiga_tasks:
                    seen_task_ids.add(taiga_task.id)

                    await sync_activity(
                        taiga_task=taiga_task,
                        taiga_story=taiga_story,
                        taiga_epic=taiga_epic,
                        kimai=kimai,
                        session=session,
                    )

    await _hide_missing_activities(
        seen_task_ids=seen_task_ids,
        kimai=kimai,
        session=session,
    )

    await _hide_missing_projects(
        seen_epic_ids=seen_epic_ids,
        kimai=kimai,
        session=session,
    )

    await _hide_missing_customers(
        seen_project_ids=seen_project_ids,
        kimai=kimai,
        session=session,
    )


async def _hide_missing_activities(
    seen_task_ids: set[int],
    kimai: KimaiClient,
    session: AsyncSession,
) -> None:
    statement = select(TaskMapping)
    mappings = (await session.execute(statement)).scalars().all()

    for mapping in mappings:
        if mapping.taiga_task_id in seen_task_ids:
            continue

        activity = await kimai.activities.get(
            mapping.kimai_activity_id,
        )

        if activity.visible:
            await kimai.activities.update(
                activity.id,
                KimaiActivityUpdate(
                    visible=False,
                ),
            )


async def _hide_missing_projects(
    seen_epic_ids: set[int],
    kimai: KimaiClient,
    session: AsyncSession,
) -> None:
    statement = select(EpicMapping)
    mappings = (await session.execute(statement)).scalars().all()

    for mapping in mappings:
        if mapping.taiga_epic_id in seen_epic_ids:
            continue

        project = await kimai.projects.get(
            mapping.kimai_project_id,
        )

        if project.visible:
            await kimai.projects.update(
                project.id,
                KimaiProjectUpdate(
                    visible=False,
                ),
            )


async def _hide_missing_customers(
    seen_project_ids: set[int],
    kimai: KimaiClient,
    session: AsyncSession,
) -> None:
    statement = select(ProjectMapping)
    mappings = (await session.execute(statement)).scalars().all()

    for mapping in mappings:
        if mapping.taiga_project_id in seen_project_ids:
            continue

        customer = await kimai.customers.get(
            mapping.kimai_customer_id,
        )

        if customer.visible:
            await kimai.customers.update(
                customer.id,
                KimaiCustomerUpdate(
                    visible=False,
                ),
            )
