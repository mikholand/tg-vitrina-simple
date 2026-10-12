from pydantic import BaseModel, ConfigDict


class ModeratorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tg_username: str | None
    tg_first_name: str | None
    tg_last_name: str | None


class ModeratorAddSchema(BaseModel):
    user_id: int
