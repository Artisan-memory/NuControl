import re

import aiohttp

from src.config import APP_VERSION

GITHUB_TAGS_URL = "https://api.github.com/repos/Artisan-memory/NuControl/tags"

_VERSION_RE = re.compile(r"\d+(?:\.\d+)*")


def as_tuple(version: str) -> tuple[int, ...]:
    """Leading numeric part of a tag: 'v0.1.2-beta' -> (0, 1, 2). The suffix is dropped
    so it is not read as an extra component making '0.0.1-beta2' look newer than '0.0.1'."""
    match = _VERSION_RE.search(version or "")
    if not match:
        return ()
    return tuple(int(part) for part in match.group().split("."))


async def get_latest_version() -> str | None:
    """Highest tag name on GitHub, or None if it can't be determined. The endpoint is
    not ordered by version, so the highest is picked rather than the first entry."""
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(GITHUB_TAGS_URL,
                                   headers={"Accept": "application/vnd.github+json"}) as response:
                if response.status != 200:
                    return None
                tags = await response.json()
    except Exception:
        return None

    names = [tag.get("name") for tag in tags if isinstance(tag, dict) and tag.get("name")]
    if not names:
        return None
    return max(names, key=as_tuple)


async def check_for_update() -> str | None:
    """Return the latest version if it is newer than the running one, else None."""
    latest = await get_latest_version()
    if latest and as_tuple(latest) > as_tuple(APP_VERSION):
        return latest
    return None
