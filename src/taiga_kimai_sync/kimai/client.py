from typing import Any, Self

import httpx

from taiga_kimai_sync.kimai.exceptions import (
    KimaiAPIError,
    KimaiAuthenticationError,
)
from taiga_kimai_sync.kimai.models import (
    KimaiActivity,
    KimaiActivityCreate,
    KimaiActivityUpdate,
    KimaiCustomer,
    KimaiCustomerCreate,
    KimaiCustomerUpdate,
    KimaiProject,
    KimaiProjectCreate,
    KimaiProjectUpdate,
)


class KimaiClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 10.0,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

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
        try:
            response = await self._client.get("/api/ping")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403}:
                raise KimaiAuthenticationError("Kimai authentication failed") from exc

            raise KimaiAPIError("Kimai API ping failed") from exc
        except httpx.HTTPError as exc:
            raise KimaiAPIError("Failed to connect to Kimai") from exc

    async def get_customers(self) -> list[KimaiCustomer]:
        response = await self._request(
            "GET",
            "/api/customers",
            params={"visible": 3},
        )

        return [KimaiCustomer.model_validate(item) for item in response.json()]

    async def create_customer(
        self,
        customer: KimaiCustomerCreate,
    ) -> KimaiCustomer:
        response = await self._request(
            "POST",
            "/api/customers",
            json=customer.model_dump(exclude_none=True),
        )

        return KimaiCustomer.model_validate(response.json())

    async def update_customer(
        self,
        customer_id: int,
        customer: KimaiCustomerUpdate,
    ) -> KimaiCustomer:
        response = await self._request(
            "PATCH",
            f"/api/customers/{customer_id}",
            json=customer.model_dump(exclude_none=True),
        )

        return KimaiCustomer.model_validate(response.json())

    async def get_projects(
        self,
        customer_id: int | None = None,
    ) -> list[KimaiProject]:
        params: dict[str, int] = {
            "visible": 3,
        }

        if customer_id is not None:
            params["customer"] = customer_id

        response = await self._request(
            "GET",
            "/api/projects",
            params=params,
        )

        return [KimaiProject.model_validate(item) for item in response.json()]

    async def create_project(
        self,
        project: KimaiProjectCreate,
    ) -> KimaiProject:
        response = await self._request(
            "POST",
            "/api/projects",
            json=project.model_dump(exclude_none=True),
        )

        return KimaiProject.model_validate(response.json())

    async def update_project(
        self,
        project_id: int,
        project: KimaiProjectUpdate,
    ) -> KimaiProject:
        response = await self._request(
            "PATCH",
            f"/api/projects/{project_id}",
            json=project.model_dump(exclude_none=True),
        )

        return KimaiProject.model_validate(response.json())

    async def get_activities(
        self,
        project_id: int | None = None,
    ) -> list[KimaiActivity]:
        params: dict[str, int] = {
            "visible": 3,
        }

        if project_id is not None:
            params["project"] = project_id

        response = await self._request(
            "GET",
            "/api/activities",
            params=params,
        )

        return [KimaiActivity.model_validate(item) for item in response.json()]

    async def create_activity(
        self,
        activity: KimaiActivityCreate,
    ) -> KimaiActivity:
        response = await self._request(
            "POST",
            "/api/activities",
            json=activity.model_dump(exclude_none=True),
        )

        return KimaiActivity.model_validate(response.json())

    async def update_activity(
        self,
        activity_id: int,
        activity: KimaiActivityUpdate,
    ) -> KimaiActivity:
        response = await self._request(
            "PATCH",
            f"/api/activities/{activity_id}",
            json=activity.model_dump(exclude_none=True),
        )

        return KimaiActivity.model_validate(response.json())

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        try:
            response = await self._client.request(
                method,
                url,
                **kwargs,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403}:
                raise KimaiAuthenticationError("Kimai authentication failed") from exc

            raise KimaiAPIError(f"Kimai API request failed: {method} {url}") from exc
        except httpx.HTTPError as exc:
            raise KimaiAPIError(f"Failed to connect to Kimai: {method} {url}") from exc

        return response

    async def close(self) -> None:
        await self._client.aclose()
