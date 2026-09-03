from typing import Any, Self

import httpx

from taiga_kimai_sync.taiga.exceptions import (
    TaigaAPIError,
    TaigaAuthenticationError,
)
from taiga_kimai_sync.taiga.models import (
    TaigaAuthResponse,
    TaigaEpic,
    TaigaProject,
)


class TaigaClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: float = 10.0,
    ) -> None:
        self._username = username
        self._password = password
        self._auth_token: str | None = None

        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
        )

    async def __aenter__(self) -> Self:
        await self.authenticate()
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        await self.close()

    async def authenticate(self) -> None:
        try:
            response = await self._client.post(
                "/api/v1/auth",
                json={
                    "type": "normal",
                    "username": self._username,
                    "password": self._password,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TaigaAuthenticationError("Failed to authenticate with Taiga") from exc

        auth = TaigaAuthResponse.model_validate(response.json())
        self._auth_token = auth.auth_token

    async def get_projects(self) -> list[TaigaProject]:
        response = await self._request(
            "GET",
            "/api/v1/projects",
        )

        return [TaigaProject.model_validate(item) for item in response.json()]

    async def get_epics(self, project_id: int) -> list[TaigaEpic]:
        response = await self._request(
            "GET",
            "/api/v1/epics",
            params={"project": project_id},
        )

        return [TaigaEpic.model_validate(item) for item in response.json()]

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        if self._auth_token is None:
            raise TaigaAuthenticationError("Taiga client is not authenticated")

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._auth_token}"

        try:
            response = await self._client.request(
                method,
                url,
                headers=headers,
                **kwargs,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TaigaAPIError(f"Taiga API request failed: {method} {url}") from exc

        return response

    async def close(self) -> None:
        await self._client.aclose()
