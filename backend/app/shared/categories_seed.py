"""Default category tree seeded on first migration.

This is NOT a platform-wide catalog shared between tenants — it is this one
store's starting category tree. The seller can hide branches it doesn't need
via `categories.is_hidden`; nothing here is multi-shop.
"""

from __future__ import annotations

FALLBACK_NAME = "Другие"

# name -> children (each child: name -> grandchildren tuple of names)
CatalogSpec = tuple[tuple[str, tuple[tuple[str, tuple[str, ...]], ...]], ...]

CATALOG: CatalogSpec = (
    ("Новогодний товар", ()),
    ("Посуда", ()),
    ("Летний товар", ()),
    ("Мыло", ()),
    ("Электросамокаты", ()),
    ("Бытовая химия", ()),
)
