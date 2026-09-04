from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taiga_kimai_sync.db.models import EpicMapping, TaskMapping
from taiga_kimai_sync.kimai.client import KimaiClient
from taiga_kimai_sync.kimai.models import (
    KimaiActivity,
    KimaiActivityCreate,
    KimaiActivityUpdate,
)
from taiga_kimai_sync.taiga.models import (
    TaigaEpic,
    TaigaTask,
    TaigaUserStory,
)


async def sync_activity(
    taiga_task: TaigaTask,
    taiga_story: TaigaUserStory,
    taiga_epic: TaigaEpic,
    kimai: KimaiClient,
    session: AsyncSession,
) -> KimaiActivity:
    _validate_relationships(
        taiga_task=taiga_task,
        taiga_story=taiga_story,
        taiga_epic=taiga_epic,
    )

    epic_mapping = await _get_epic_mapping(
        session=session,
        taiga_epic_id=taiga_epic.id,
    )

    if epic_mapping is None:
        raise RuntimeError(f"Epic mapping not found for Taiga epic {taiga_epic.id}")

    activity_name = _build_activity_name(
        taiga_story=taiga_story,
        taiga_task=taiga_task,
    )

    task_mapping = await _get_task_mapping(
        session=session,
        taiga_task_id=taiga_task.id,
    )

    if task_mapping is None:
        return await _create_activity(
            taiga_task=taiga_task,
            activity_name=activity_name,
            kimai_project_id=epic_mapping.kimai_project_id,
            kimai=kimai,
            session=session,
        )

    activity = await kimai.activities.get(
        task_mapping.kimai_activity_id,
    )

    visible = not taiga_task.is_closed

    if (
        activity.name != activity_name
        or activity.project != epic_mapping.kimai_project_id
        or activity.visible != visible
    ):
        activity = await kimai.activities.update(
            activity.id,
            KimaiActivityUpdate(
                name=activity_name,
                project=epic_mapping.kimai_project_id,
                visible=visible,
            ),
        )

    return activity


def _validate_relationships(
    taiga_task: TaigaTask,
    taiga_story: TaigaUserStory,
    taiga_epic: TaigaEpic,
) -> None:
    if taiga_task.user_story != taiga_story.id:
        raise RuntimeError(
            f"Taiga task {taiga_task.id} does not belong to user story {taiga_story.id}"
        )

    if taiga_story.project != taiga_epic.project:
        raise RuntimeError(
            f"Taiga user story {taiga_story.id} and "
            f"epic {taiga_epic.id} belong to different projects"
        )


def _build_activity_name(
    taiga_story: TaigaUserStory,
    taiga_task: TaigaTask,
) -> str:
    return f"[{taiga_story.subject}] {taiga_task.subject}"


async def _get_epic_mapping(
    session: AsyncSession,
    taiga_epic_id: int,
) -> EpicMapping | None:
    statement = select(EpicMapping).where(
        EpicMapping.taiga_epic_id == taiga_epic_id,
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def _get_task_mapping(
    session: AsyncSession,
    taiga_task_id: int,
) -> TaskMapping | None:
    statement = select(TaskMapping).where(
        TaskMapping.taiga_task_id == taiga_task_id,
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def _create_activity(
    taiga_task: TaigaTask,
    activity_name: str,
    kimai_project_id: int,
    kimai: KimaiClient,
    session: AsyncSession,
) -> KimaiActivity:
    activity = await kimai.activities.create(
        KimaiActivityCreate(
            name=activity_name,
            project=kimai_project_id,
            visible=not taiga_task.is_closed,
        )
    )

    mapping = TaskMapping(
        taiga_task_id=taiga_task.id,
        kimai_activity_id=activity.id,
    )

    session.add(mapping)
    await session.commit()

    return activity
