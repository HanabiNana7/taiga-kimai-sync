from pydantic import BaseModel, ConfigDict


class TaigaAuthResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    auth_token: str


class TaigaProject(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    slug: str


class TaigaEpic(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    ref: int
    subject: str
    project: int


class TaigaUserStory(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    ref: int
    subject: str
    project: int
    status: int
    is_closed: bool


class TaigaTask(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    ref: int
    subject: str
    project: int
    user_story: int | None
    status: int
    is_closed: bool
