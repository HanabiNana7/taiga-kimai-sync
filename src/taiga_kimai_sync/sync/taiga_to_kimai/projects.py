from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taiga_kimai_sync.db.models import EpicMapping, ProjectMapping
from taiga_kimai_sync.kimai.client import KimaiClient
from taiga_kimai_sync.kimai.models import (
    KimaiProject,
    KimaiProjectCreate,
    KimaiProjectUpdate,
)
from taiga_kimai_sync.taiga.models import TaigaEpic


async def sync_project(
    taiga_epic: TaigaEpic,
    kimai: KimaiClient,
    session: AsyncSession,
) -> KimaiProject:
    project_mapping = await _get_project_mapping(
        session=session,
        taiga_project_id=taiga_epic.project,
    )

    if project_mapping is None:
        raise RuntimeError(
            f"Project mapping not found for Taiga project {taiga_epic.project}"
        )

    epic_mapping = await _get_epic_mapping(
        session=session,
        taiga_epic_id=taiga_epic.id,
    )

    if epic_mapping is None:
        return await _create_project(
            taiga_epic=taiga_epic,
            kimai_customer_id=project_mapping.kimai_customer_id,
            kimai=kimai,
            session=session,
        )

    project = await kimai.projects.get(
        epic_mapping.kimai_project_id,
    )

    if (
        project.name != taiga_epic.subject
        or project.customer != project_mapping.kimai_customer_id
        or not project.visible
    ):
        project = await kimai.projects.update(
            project.id,
            KimaiProjectUpdate(
                name=taiga_epic.subject,
                customer=project_mapping.kimai_customer_id,
                visible=True,
            ),
        )

    return project


async def _get_project_mapping(
    session: AsyncSession,
    taiga_project_id: int,
) -> ProjectMapping | None:
    statement = select(ProjectMapping).where(
        ProjectMapping.taiga_project_id == taiga_project_id,
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def _get_epic_mapping(
    session: AsyncSession,
    taiga_epic_id: int,
) -> EpicMapping | None:
    statement = select(EpicMapping).where(
        EpicMapping.taiga_epic_id == taiga_epic_id,
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def _create_project(
    taiga_epic: TaigaEpic,
    kimai_customer_id: int,
    kimai: KimaiClient,
    session: AsyncSession,
) -> KimaiProject:
    project = await kimai.projects.create(
        KimaiProjectCreate(
            name=taiga_epic.subject,
            customer=kimai_customer_id,
            visible=True,
        )
    )

    mapping = EpicMapping(
        taiga_epic_id=taiga_epic.id,
        kimai_project_id=project.id,
    )

    session.add(mapping)
    await session.commit()

    return project
