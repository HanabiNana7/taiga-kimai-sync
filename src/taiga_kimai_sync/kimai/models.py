from pydantic import BaseModel, ConfigDict


class KimaiCustomer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    visible: bool


class KimaiCustomerCreate(BaseModel):
    name: str
    visible: bool = True


class KimaiCustomerUpdate(BaseModel):
    name: str | None = None
    visible: bool | None = None
