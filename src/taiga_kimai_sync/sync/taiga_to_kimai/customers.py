from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taiga_kimai_sync.db.models import ProjectMapping
from taiga_kimai_sync.kimai.client import KimaiClient
from taiga_kimai_sync.kimai.models import (
    KimaiCustomer,
    KimaiCustomerCreate,
    KimaiCustomerUpdate,
)
from taiga_kimai_sync.taiga.models import TaigaProject


async def sync_customer(
    taiga_project: TaigaProject,
    kimai: KimaiClient,
    session: AsyncSession,
) -> KimaiCustomer:
    mapping = await _get_mapping(
        session=session,
        taiga_project_id=taiga_project.id,
    )

    if mapping is None:
        return await _create_customer(
            taiga_project=taiga_project,
            kimai=kimai,
            session=session,
        )

    customer = await kimai.customers.get(
        mapping.kimai_customer_id,
    )

    if customer.name != taiga_project.name or not customer.visible:
        customer = await kimai.customers.update(
            customer.id,
            KimaiCustomerUpdate(
                name=taiga_project.name,
                visible=True,
            ),
        )

    return customer


async def _get_mapping(
    session: AsyncSession,
    taiga_project_id: int,
) -> ProjectMapping | None:
    statement = select(ProjectMapping).where(
        ProjectMapping.taiga_project_id == taiga_project_id,
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def _create_customer(
    taiga_project: TaigaProject,
    kimai: KimaiClient,
    session: AsyncSession,
) -> KimaiCustomer:
    customer = await kimai.customers.create(
        KimaiCustomerCreate(
            name=taiga_project.name,
            visible=True,
        )
    )

    mapping = ProjectMapping(
        taiga_project_id=taiga_project.id,
        kimai_customer_id=customer.id,
    )

    session.add(mapping)
    await session.commit()

    return customer
