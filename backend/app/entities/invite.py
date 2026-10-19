from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin


class Invite(Base, TimestampMixin):
    """A one-time link that promotes whoever opens it to moderator.

    Single-tenant, like `Contact`/`Banner` — no shop scoping. `create()`
    (in the repository) invalidates any previously-outstanding invite before
    minting a new one, so at most one link is ever live: sharing a "new"
    link should supersede whatever was shared before, not add to it.
    """

    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    used_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
