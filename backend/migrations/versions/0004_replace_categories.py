"""Replace the seeded category tree with the seller's actual catalog.

The original 0001 tree (Одежда/Обувь/Электроника/...) was a generic
placeholder, never the real catalog. The seller wants exactly these flat
categories instead: Новогодний товар, Посуда, летний товар, Мыло,
Электросомокати, Бытовая Химия, plus the mandatory fallback (now named
"Другие" instead of "Другое").

This drops every existing category row (cascades into `product_categories`,
so any product tagged with an old category simply loses that tag — no
product rows are touched) and reseeds from the updated
`app.shared.categories_seed.CATALOG`.

Revision ID: 0004_replace_categories
Revises: 0003_banners
Create Date: 2026-10-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.shared.categories_seed import CATALOG, FALLBACK_NAME
from app.shared.slug import category_code

revision: str = "0004_replace_categories"
down_revision: str | None = "0003_banners"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The tree this migration replaces — kept here (not imported) so downgrade()
# can restore it without depending on whatever categories_seed.py looks like
# by the time someone runs it.
_OLD_FALLBACK_NAME = "Другое"
_OLD_CATALOG: tuple[tuple[str, tuple[tuple[str, tuple[str, ...]], ...]], ...] = (
    (
        "Одежда",
        (
            ("Верхняя одежда", ("Куртки", "Пуховики", "Пальто")),
            ("Платья и юбки", ()),
            ("Футболки и рубашки", ()),
        ),
    ),
    (
        "Обувь",
        (
            ("Кроссовки", ()),
            ("Ботинки", ()),
            ("Туфли", ()),
        ),
    ),
    (
        "Электроника",
        (
            ("Телефоны и аксессуары", ()),
            ("Ноутбуки и компьютеры", ()),
        ),
    ),
    (
        "Дом и быт",
        (
            ("Кухня", ()),
            ("Текстиль", ()),
        ),
    ),
    ("Детские товары", ()),
    ("Красота и здоровье", ()),
)


def _reseed(catalog: tuple, fallback_name: str) -> None:
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

    for top_order, (top_name, children) in enumerate(catalog):
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
            "name": fallback_name,
            "code": category_code(fallback_name, None),
            "sort_order": len(catalog),
            "depth": 0,
            "is_fallback": True,
            "is_hidden": False,
        }
    )

    op.bulk_insert(categories, rows)
    op.execute(f"SELECT setval('categories_id_seq', {fallback_id}, true)")


def upgrade() -> None:
    # Cascades into product_categories; products themselves are untouched.
    op.execute("DELETE FROM categories")
    _reseed(CATALOG, FALLBACK_NAME)


def downgrade() -> None:
    op.execute("DELETE FROM categories")
    _reseed(_OLD_CATALOG, _OLD_FALLBACK_NAME)
