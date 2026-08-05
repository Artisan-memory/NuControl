import asyncio
import subprocess

# Без этого флага на каждый tasklist/taskkill/shutdown мигает окно консоли
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def run(args, **kwargs):
    kwargs.setdefault("creationflags", NO_WINDOW)
    return subprocess.run(args, **kwargs)


async def run_async(args, **kwargs):
    return await asyncio.to_thread(lambda: run(args, **kwargs))
