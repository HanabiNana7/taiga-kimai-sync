from sqlalchemy.orm import Mapped, mapped_column

from taiga_kimai_sync.db.base import Base


class ProjectMapping(Base):
    __tablename__ = "project_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)

    taiga_project_id: Mapped[int] = mapped_column(
        unique=True,
        index=True,
    )

    kimai_customer_id: Mapped[int] = mapped_column(
        unique=True,
        index=True,
    )


class EpicMapping(Base):
    __tablename__ = "epic_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)

    taiga_epic_id: Mapped[int] = mapped_column(
        unique=True,
        index=True,
    )

    kimai_project_id: Mapped[int] = mapped_column(
        unique=True,
        index=True,
    )


class TaskMapping(Base):
    __tablename__ = "task_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)

    taiga_task_id: Mapped[int] = mapped_column(
        unique=True,
        index=True,
    )

    kimai_activity_id: Mapped[int] = mapped_column(
        unique=True,
        index=True,
    )
