import re

_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "",
    "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

_NON_SLUG_CHARS = re.compile(r"[^a-z0-9-]+")
_DASH_COLLAPSE = re.compile(r"-+")


def slugify(text: str) -> str:
    lowered = text.strip().lower()
    translit = "".join(_TRANSLIT.get(ch, ch) for ch in lowered)
    translit = translit.replace(" ", "-")
    translit = _NON_SLUG_CHARS.sub("", translit)
    translit = _DASH_COLLAPSE.sub("-", translit).strip("-")
    return translit or "category"


def category_code(name: str, parent_code: str | None) -> str:
    slug = slugify(name)
    return f"{parent_code}.{slug}" if parent_code else slug
