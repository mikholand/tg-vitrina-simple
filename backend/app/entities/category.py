from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base

MAX_CATEGORY_DEPTH = 2  # 0, 1, 2 -> max 3 levels


class Category(Base):
    """A plain tree, local to this one store. No per-shop visibility table —
    hiding a branch is a single boolean on the row itself."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(300), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    depth: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        CheckConstraint(f"depth >= 0 AND depth <= {MAX_CATEGORY_DEPTH}", name="ck_categories_depth"),
        UniqueConstraint("parent_id", "name", name="uq_categories_parent_name"),
        Index("ix_categories_parent_id", "parent_id"),
    )


class ProductCategory(Base):
    """Product <-> category M2M. A product can be filed under several leaves."""

    __tablename__ = "product_categories"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True
    )
