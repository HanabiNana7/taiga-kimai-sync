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


class KimaiProject(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    customer: int
    visible: bool


class KimaiProjectCreate(BaseModel):
    name: str
    customer: int
    visible: bool = True


class KimaiProjectUpdate(BaseModel):
    name: str | None = None
    customer: int | None = None
    visible: bool | None = None


class KimaiActivity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    project: int | None = None
    visible: bool


class KimaiActivityCreate(BaseModel):
    name: str
    project: int
    visible: bool = True


class KimaiActivityUpdate(BaseModel):
    name: str | None = None
    project: int | None = None
    visible: bool | None = None
