from pydantic import BaseModel, ConfigDict


class TaigaAuthResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    auth_token: str


class TaigaProject(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    slug: str
