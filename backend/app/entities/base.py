from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    # Without this, `updated_at` (onupdate=func.now()) is left expired after
    # any UPDATE and the next *synchronous* attribute read (e.g. Pydantic's
    # `model_validate` serializing the ORM object right after a flush, with
    # no further `await`) raises `MissingGreenlet` — async SQLAlchemy cannot
    # lazy-load outside of an awaited call. Eager-fetching the server-side
    # default/onupdate value as part of the (already awaited) flush avoids
    # that lazy load entirely. Affects every backend, not just SQLite.
    __mapper_args__ = {"eager_defaults": True}

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
