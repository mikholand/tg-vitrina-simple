from pydantic import BaseModel, ConfigDict


class CategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int | None
    name: str
    code: str
    sort_order: int
    depth: int
    is_fallback: bool
    is_hidden: bool


class CategoryVisibilityUpdateSchema(BaseModel):
    is_hidden: bool


class CategoryCreateSchema(BaseModel):
    name: str
    parent_id: int | None = None


class CategoryUpdateSchema(BaseModel):
    name: str
