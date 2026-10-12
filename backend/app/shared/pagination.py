from pydantic import BaseModel


class Paginated[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
