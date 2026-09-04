from typing import Any

import httpx

from taiga_kimai_sync.kimai.exceptions import (
    KimaiAPIError,
    KimaiAuthenticationError,
)


class KimaiTransport:
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

    async def ping(self) -> None:
        await self.request(
            "GET",
            "/api/ping",
        )

    async def request(
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
