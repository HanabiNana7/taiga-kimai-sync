from typing import Self

from taiga_kimai_sync.kimai.activities import ActivitiesResource
from taiga_kimai_sync.kimai.customers import CustomersResource
from taiga_kimai_sync.kimai.projects import ProjectsResource
from taiga_kimai_sync.kimai.transport import KimaiTransport


class KimaiClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 10.0,
    ) -> None:
        self._transport = KimaiTransport(
            base_url=base_url,
            token=token,
            timeout=timeout,
        )

        self.customers = CustomersResource(self._transport)
        self.projects = ProjectsResource(self._transport)
        self.activities = ActivitiesResource(self._transport)

    async def __aenter__(self) -> Self:
        await self.ping()
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        await self.close()

    async def ping(self) -> None:
        await self._transport.ping()

    async def close(self) -> None:
        await self._transport.close()
