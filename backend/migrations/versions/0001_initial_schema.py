"""Initial schema: single-shop storefront.

No `shops` table, no `shop_id` column anywhere — this deployment serves
exactly one store, configured via environment variables.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.shared.categories_seed import CATALOG, FALLBACK_NAME
from app.shared.slug import category_code

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tg_username", sa.String(64)),
        sa.Column("tg_first_name", sa.String(128)),
        sa.Column("tg_last_name", sa.String(128)),
        sa.Column("role", sa.String(20), nullable=False, server_default="customer"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "raw_posts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("media_group_id", sa.BigInteger()),
        sa.Column("raw_text", sa.Text()),
        sa.Column("photo_paths", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("product_id", sa.BigInteger()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_raw_posts_status", "raw_posts", ["status"])
    op.create_index(
        "uq_raw_posts_media_group",
        "raw_posts",
        ["channel_id", "media_group_id"],
        unique=True,
        postgresql_where=sa.text("media_group_id IS NOT NULL"),
    )
    op.create_index(
        "uq_raw_posts_message",
        "raw_posts",
        ["channel_id", "message_id"],
        unique=True,
        postgresql_where=sa.text("media_group_id IS NULL"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("price", sa.Numeric(12, 2)),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("description", sa.Text()),
        sa.Column("sku", sa.String(100)),
        sa.Column("availability", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("quantity", sa.Integer()),
        sa.Column("photo_paths", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("edited_by_seller", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "source_post_id",
            sa.BigInteger(),
            sa.ForeignKey("raw_posts.id", ondelete="SET NULL"),
        ),
        sa.Column("publish_to_channel", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("channel_message_id", sa.BigInteger()),
        sa.Column("views_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "quantity IS NULL OR quantity >= 0", name="ck_products_quantity_non_negative"
        ),
    )
    op.create_index("ix_products_status", "products", ["status"])
    op.create_index("ix_products_sku", "products", ["sku"])
    op.execute(
        "CREATE INDEX ix_products_name_trgm ON products "
        "USING GIN (name gin_trgm_ops)"
    )

    op.create_foreign_key(
        "fk_raw_posts_product_id",
        "raw_posts",
        "products",
        ["product_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(300), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("depth", sa.SmallInteger(), nullable=False),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint("depth >= 0 AND depth <= 2", name="ck_categories_depth"),
        sa.UniqueConstraint("parent_id", "name", name="uq_categories_parent_name"),
    )
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])
    op.create_index(
        "uq_categories_single_fallback",
        "categories",
        ["is_fallback"],
        unique=True,
        postgresql_where=sa.text("is_fallback = true"),
    )

    op.create_table(
        "product_categories",
        sa.Column(
            "product_id",
            sa.BigInteger(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("categories.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "favorites",
        sa.Column(
            "user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column(
            "product_id",
            sa.BigInteger(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "store_views",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("visitor_key", sa.Uuid()),
        sa.Column("view_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "(user_id IS NULL) <> (visitor_key IS NULL)", name="ck_store_views_one_identity"
        ),
    )
    op.create_index("ix_store_views_view_date", "store_views", ["view_date"])
    op.execute(
        "CREATE UNIQUE INDEX uq_store_views_dedup ON store_views "
        "(COALESCE(user_id, -1), COALESCE(visitor_key, '00000000-0000-0000-0000-000000000000'), view_date)"
    )

    op.create_table(
        "product_views",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "product_id",
            sa.BigInteger(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("visitor_key", sa.Uuid()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "(user_id IS NULL) <> (visitor_key IS NULL)", name="ck_product_views_one_identity"
        ),
    )
    op.create_index("ix_product_views_product_id", "product_views", ["product_id"])

    op.create_table(
        "sync_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="idle"),
        sa.Column("cursor", sa.BigInteger()),
        sa.Column("stop_id", sa.BigInteger()),
        sa.Column("done_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_count", sa.Integer()),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_at", sa.DateTime(timezone=True)),
        sa.Column("stop_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_error", sa.String(200)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    _seed_categories()


def _seed_categories() -> None:
    categories = sa.table(
        "categories",
        sa.column("id", sa.Integer()),
        sa.column("parent_id", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("code", sa.String()),
        sa.column("sort_order", sa.Integer()),
        sa.column("depth", sa.SmallInteger()),
        sa.column("is_fallback", sa.Boolean()),
        sa.column("is_hidden", sa.Boolean()),
    )

    rows: list[dict] = []
    next_id = 1

    def add(name: str, parent_id: int | None, parent_code: str | None, depth: int, order: int) -> int:
        nonlocal next_id
        row_id = next_id
        next_id += 1
        rows.append(
            {
                "id": row_id,
                "parent_id": parent_id,
                "name": name,
                "code": category_code(name, parent_code),
                "sort_order": order,
                "depth": depth,
                "is_fallback": False,
                "is_hidden": False,
            }
        )
        return row_id

    for top_order, (top_name, children) in enumerate(CATALOG):
        top_id = add(top_name, None, None, 0, top_order)
        top_code = rows[top_id - 1]["code"]
        for mid_order, (mid_name, grandchildren) in enumerate(children):
            mid_id = add(mid_name, top_id, top_code, 1, mid_order)
            mid_code = rows[mid_id - 1]["code"]
            for leaf_order, leaf_name in enumerate(grandchildren):
                add(leaf_name, mid_id, mid_code, 2, leaf_order)

    fallback_id = next_id
    rows.append(
        {
            "id": fallback_id,
            "parent_id": None,
            "name": FALLBACK_NAME,
            "code": category_code(FALLBACK_NAME, None),
            "sort_order": len(CATALOG),
            "depth": 0,
            "is_fallback": True,
            "is_hidden": False,
        }
    )

    op.bulk_insert(categories, rows)
    op.execute(f"SELECT setval('categories_id_seq', {fallback_id}, true)")


def downgrade() -> None:
    op.drop_table("sync_state")
    op.drop_table("product_views")
    op.drop_table("store_views")
    op.drop_table("favorites")
    op.drop_table("product_categories")
    op.drop_table("categories")
    op.drop_constraint("fk_raw_posts_product_id", "raw_posts", type_="foreignkey")
    op.drop_table("products")
    op.drop_table("raw_posts")
    op.drop_table("users")
