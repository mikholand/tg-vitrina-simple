"""Fix spelling typos in three seeded category names.

0004_replace_categories seeded "летний товар" (lowercase, inconsistent with
its siblings), "Электросомокати" (misspelled — should be "самокаты", not
"сомокати"), and "Бытовая Химия" (second word wrongly capitalized). This
corrects all three, matching on the exact old (misspelled) name so a seller
who already renamed one of these categories themselves is left untouched —
only rows still carrying the original seeded typo get updated.

`code` (the slug derived from `name`) only actually changes for the
"электросомокати" -> "электросамокаты" row; the other two renames are
case-only and slugify() lowercases anyway, so their code is unaffected.

Revision ID: 0006_fix_category_typos
Revises: 0005_product_video
Create Date: 2026-10-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_fix_category_typos"
down_revision: str | None = "0005_product_video"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (old name, new name, old code, new code)
_RENAMES: tuple[tuple[str, str, str, str], ...] = (
    ("летний товар", "Летний товар", "letniy-tovar", "letniy-tovar"),
    ("Электросомокати", "Электросамокаты", "electrosomokati", "electrosamokaty"),
    ("Бытовая Химия", "Бытовая химия", "bytovaya-himiya", "bytovaya-himiya"),
)


def upgrade() -> None:
    bind = op.get_bind()
    for old_name, new_name, _old_code, new_code in _RENAMES:
        bind.execute(
            sa.text("UPDATE categories SET name = :new_name, code = :new_code WHERE name = :old_name"),
            {"new_name": new_name, "new_code": new_code, "old_name": old_name},
        )


def downgrade() -> None:
    bind = op.get_bind()
    for old_name, new_name, old_code, _new_code in _RENAMES:
        bind.execute(
            sa.text("UPDATE categories SET name = :old_name, code = :old_code WHERE name = :new_name"),
            {"old_name": old_name, "old_code": old_code, "new_name": new_name},
        )
