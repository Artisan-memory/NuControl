import os
from itertools import count

PAGE_SIZE = 30
# Больше пути в кэше держать незачем, а расти бесконечно он не должен
MAX_TOKENS = 4000

_by_token: dict[str, str] = {}
_by_path: dict[str, str] = {}
_counter = count(1)


def token_for(path: str) -> str:
    """Короткий ключ вместо пути: в start-payload влезает 64 символа, а путь длиннее"""
    path = os.path.abspath(path)
    if path in _by_path:
        return _by_path[path]

    if len(_by_token) >= MAX_TOKENS:
        _by_token.clear()
        _by_path.clear()

    token = f"p{next(_counter)}"
    _by_token[token] = path
    _by_path[path] = token
    return token


def path_for(token: str) -> str | None:
    return _by_token.get(token)


def _sort_key(entry: os.DirEntry) -> tuple[int, str]:
    return (0 if entry.is_dir() else 1, entry.name.lower())


def read_dir(directory: str) -> list[os.DirEntry]:
    with os.scandir(directory) as entries:
        # Права на отдельные элементы проверять не нужно, is_dir сам вернёт False
        return sorted(entries, key=_sort_key)


def page_count(total: int) -> int:
    return max(1, -(-total // PAGE_SIZE))


def slice_page(entries: list, page: int) -> list:
    page = max(0, min(page, page_count(len(entries)) - 1))
    return entries[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
