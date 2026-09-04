from taiga_kimai_sync.kimai.models import (
    KimaiActivity,
    KimaiActivityCreate,
    KimaiActivityUpdate,
)
from taiga_kimai_sync.kimai.transport import KimaiTransport


class ActivitiesResource:
    def __init__(self, transport: KimaiTransport) -> None:
        self._transport = transport

    async def list(
        self,
        project_id: int | None = None,
    ) -> list[KimaiActivity]:
        params: dict[str, int] = {
            "visible": 3,
        }

        if project_id is not None:
            params["project"] = project_id

        response = await self._transport.request(
            "GET",
            "/api/activities",
            params=params,
        )

        return [KimaiActivity.model_validate(item) for item in response.json()]

    async def get(self, activity_id: int) -> KimaiActivity:
        response = await self._transport.request(
            "GET",
            f"/api/activities/{activity_id}",
        )

        return KimaiActivity.model_validate(response.json())

    async def create(
        self,
        activity: KimaiActivityCreate,
    ) -> KimaiActivity:
        response = await self._transport.request(
            "POST",
            "/api/activities",
            json=activity.model_dump(exclude_none=True),
        )

        return KimaiActivity.model_validate(response.json())

    async def update(
        self,
        activity_id: int,
        activity: KimaiActivityUpdate,
    ) -> KimaiActivity:
        response = await self._transport.request(
            "PATCH",
            f"/api/activities/{activity_id}",
            json=activity.model_dump(exclude_none=True),
        )

        return KimaiActivity.model_validate(response.json())
