from app.entities.category import Category
from app.repositories.category import CategoryRepository

PATH_SEPARATOR = " / "


class CategoryService:
    def __init__(self, category_repository: CategoryRepository) -> None:
        self._category_repository = category_repository

    @staticmethod
    def _path_label(category: Category, by_id: dict[int, Category]) -> str:
        parts = [category.name]
        parent_id = category.parent_id
        while parent_id is not None:
            parent = by_id[parent_id]
            parts.append(parent.name)
            parent_id = parent.parent_id
        return PATH_SEPARATOR.join(reversed(parts))

    async def list_tree(self, include_hidden: bool = True) -> list[Category]:
        categories = await self._category_repository.list_all()
        if include_hidden:
            return categories
        return [c for c in categories if not c.is_hidden]

    async def list_selectable_paths(self) -> dict[str, Category]:
        """Label -> Category for every visible, non-fallback category. This
        is exactly the menu handed to the LLM — it may choose only from here.
        """
        categories = await self._category_repository.list_all()
        by_id = {c.id: c for c in categories}
        return {
            self._path_label(c, by_id): c
            for c in categories
            if not c.is_hidden and not c.is_fallback
        }

    async def resolve_label(self, label: str | None) -> Category:
        """Map the LLM's chosen label back to a Category row. Any answer
        that isn't an exact match against the menu we gave it — including
        a made-up category — falls back to "Другие". The LLM has no
        authority to create categories.
        """
        fallback = await self._category_repository.get_fallback()
        if fallback is None:
            raise RuntimeError("fallback category 'Другое' is missing — run migrations/seed")

        if not label:
            return fallback

        paths = await self.list_selectable_paths()
        category = paths.get(label.strip())
        if category is None:
            return fallback

        # Defensive: if it somehow got hidden since the menu was built, climb up.
        categories = await self._category_repository.list_all()
        by_id = {c.id: c for c in categories}
        node: Category | None = category
        while node is not None and node.is_hidden:
            node = by_id.get(node.parent_id) if node.parent_id else None
        return node if node is not None else fallback

    async def set_hidden(self, category_id: int, is_hidden: bool) -> None:
        category = await self._category_repository.get(category_id)
        if category is not None and category.is_fallback and is_hidden:
            raise ValueError("the fallback category 'Другое' cannot be hidden")
        await self._category_repository.set_hidden(category_id, is_hidden)
