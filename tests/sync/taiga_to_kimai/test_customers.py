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
from taiga_kimai_sync.db.models import ProjectMapping
from taiga_kimai_sync.kimai.models import KimaiCustomer
from taiga_kimai_sync.sync.taiga_to_kimai.customers import sync_customer
from taiga_kimai_sync.taiga.models import TaigaProject


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
async def test_create_customer_and_mapping(
    session: AsyncSession,
) -> None:
    taiga_project = TaigaProject(
        id=12,
        name="AI Department",
        slug="ai-department",
    )

    created_customer = KimaiCustomer(
        id=37,
        name="AI Department",
        visible=True,
    )

    customers = SimpleNamespace(
        get=AsyncMock(),
        create=AsyncMock(return_value=created_customer),
        update=AsyncMock(),
    )
    kimai = SimpleNamespace(customers=customers)

    result = await sync_customer(
        taiga_project=taiga_project,
        kimai=kimai,
        session=session,
    )

    assert result == created_customer

    customers.create.assert_awaited_once()
    customers.get.assert_not_awaited()
    customers.update.assert_not_awaited()

    query = select(ProjectMapping).where(
        ProjectMapping.taiga_project_id == taiga_project.id,
    )
    mapping = (await session.execute(query)).scalar_one()

    assert mapping.taiga_project_id == 12
    assert mapping.kimai_customer_id == 37


@pytest.mark.asyncio
async def test_existing_customer_is_not_created_again(
    session: AsyncSession,
) -> None:
    mapping = ProjectMapping(
        taiga_project_id=12,
        kimai_customer_id=37,
    )
    session.add(mapping)
    await session.commit()

    taiga_project = TaigaProject(
        id=12,
        name="AI Department",
        slug="ai-department",
    )

    existing_customer = KimaiCustomer(
        id=37,
        name="AI Department",
        visible=True,
    )

    customers = SimpleNamespace(
        get=AsyncMock(return_value=existing_customer),
        create=AsyncMock(),
        update=AsyncMock(),
    )
    kimai = SimpleNamespace(customers=customers)

    result = await sync_customer(
        taiga_project=taiga_project,
        kimai=kimai,
        session=session,
    )

    assert result == existing_customer

    customers.get.assert_awaited_once_with(37)
    customers.create.assert_not_awaited()
    customers.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_customer_name_is_updated(
    session: AsyncSession,
) -> None:
    mapping = ProjectMapping(
        taiga_project_id=12,
        kimai_customer_id=37,
    )
    session.add(mapping)
    await session.commit()

    taiga_project = TaigaProject(
        id=12,
        name="AI Research Department",
        slug="ai-department",
    )

    existing_customer = KimaiCustomer(
        id=37,
        name="AI Department",
        visible=True,
    )

    updated_customer = KimaiCustomer(
        id=37,
        name="AI Research Department",
        visible=True,
    )

    customers = SimpleNamespace(
        get=AsyncMock(return_value=existing_customer),
        create=AsyncMock(),
        update=AsyncMock(return_value=updated_customer),
    )
    kimai = SimpleNamespace(customers=customers)

    result = await sync_customer(
        taiga_project=taiga_project,
        kimai=kimai,
        session=session,
    )

    assert result == updated_customer
    assert result.id == 37

    customers.create.assert_not_awaited()
    customers.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_hidden_customer_is_made_visible(
    session: AsyncSession,
) -> None:
    mapping = ProjectMapping(
        taiga_project_id=12,
        kimai_customer_id=37,
    )
    session.add(mapping)
    await session.commit()

    taiga_project = TaigaProject(
        id=12,
        name="AI Department",
        slug="ai-department",
    )

    hidden_customer = KimaiCustomer(
        id=37,
        name="AI Department",
        visible=False,
    )

    visible_customer = KimaiCustomer(
        id=37,
        name="AI Department",
        visible=True,
    )

    customers = SimpleNamespace(
        get=AsyncMock(return_value=hidden_customer),
        create=AsyncMock(),
        update=AsyncMock(return_value=visible_customer),
    )
    kimai = SimpleNamespace(customers=customers)

    result = await sync_customer(
        taiga_project=taiga_project,
        kimai=kimai,
        session=session,
    )

    assert result.visible is True

    customers.create.assert_not_awaited()
    customers.update.assert_awaited_once()
