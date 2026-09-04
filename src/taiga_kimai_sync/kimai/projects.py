from taiga_kimai_sync.kimai.models import (
    KimaiProject,
    KimaiProjectCreate,
    KimaiProjectUpdate,
)
from taiga_kimai_sync.kimai.transport import KimaiTransport


class ProjectsResource:
    def __init__(self, transport: KimaiTransport) -> None:
        self._transport = transport

    async def list(
        self,
        customer_id: int | None = None,
    ) -> list[KimaiProject]:
        params: dict[str, int] = {
            "visible": 3,
        }

        if customer_id is not None:
            params["customer"] = customer_id

        response = await self._transport.request(
            "GET",
            "/api/projects",
            params=params,
        )

        return [KimaiProject.model_validate(item) for item in response.json()]

    async def get(self, project_id: int) -> KimaiProject:
        response = await self._transport.request(
            "GET",
            f"/api/projects/{project_id}",
        )

        return KimaiProject.model_validate(response.json())

    async def create(
        self,
        project: KimaiProjectCreate,
    ) -> KimaiProject:
        response = await self._transport.request(
            "POST",
            "/api/projects",
            json=project.model_dump(exclude_none=True),
        )

        return KimaiProject.model_validate(response.json())

    async def update(
        self,
        project_id: int,
        project: KimaiProjectUpdate,
    ) -> KimaiProject:
        response = await self._transport.request(
            "PATCH",
            f"/api/projects/{project_id}",
            json=project.model_dump(exclude_none=True),
        )

        return KimaiProject.model_validate(response.json())
