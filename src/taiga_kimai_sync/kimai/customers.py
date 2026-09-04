from taiga_kimai_sync.kimai.models import (
    KimaiCustomer,
    KimaiCustomerCreate,
    KimaiCustomerUpdate,
)
from taiga_kimai_sync.kimai.transport import KimaiTransport


class CustomersResource:
    def __init__(self, transport: KimaiTransport) -> None:
        self._transport = transport

    async def list(self) -> list[KimaiCustomer]:
        response = await self._transport.request(
            "GET",
            "/api/customers",
            params={"visible": 3},
        )

        return [KimaiCustomer.model_validate(item) for item in response.json()]

    async def get(self, customer_id: int) -> KimaiCustomer:
        response = await self._transport.request(
            "GET",
            f"/api/customers/{customer_id}",
        )

        return KimaiCustomer.model_validate(response.json())

    async def create(
        self,
        customer: KimaiCustomerCreate,
    ) -> KimaiCustomer:
        response = await self._transport.request(
            "POST",
            "/api/customers",
            json=customer.model_dump(exclude_none=True),
        )

        return KimaiCustomer.model_validate(response.json())

    async def update(
        self,
        customer_id: int,
        customer: KimaiCustomerUpdate,
    ) -> KimaiCustomer:
        response = await self._transport.request(
            "PATCH",
            f"/api/customers/{customer_id}",
            json=customer.model_dump(exclude_none=True),
        )

        return KimaiCustomer.model_validate(response.json())
