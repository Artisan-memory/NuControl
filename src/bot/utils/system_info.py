"""Raw hardware readings for /check and /cpu. Returns plain numbers; formatting and
translation happen in the command layer so both reports share one source."""

import asyncio
import getpass
import platform
import shutil

import psutil

from src.bot.utils import process


async def get_platform_info() -> dict[str, str]:
    return {
        "os": f"{platform.system()} {platform.release()}".strip(),
        "host": platform.node(),
        "user": getpass.getuser(),
        # processor() is empty on some Windows builds; machine() is never empty
        "cpu": platform.processor() or platform.machine(),
        "python": platform.python_version(),
    }


async def get_memory_info() -> dict[str, float]:
    """Same total/used/free/percent shape as the disks so both render through one path.
    `free` is psutil's `available` - memory that can actually be handed out."""
    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "used": memory.used,
        "free": memory.available,
        "percent": memory.percent,
    }


async def get_disks_info() -> list[dict[str, float | str]]:
    disks = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except OSError:
            # Пустой картридер или дисковод тоже в списке, но прочитать их нельзя
            continue
        disks.append({
            "name": partition.device,
            "fstype": partition.fstype,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent,
        })
    return disks


async def get_disk_totals() -> dict[str, float]:
    """Every readable partition summed up, for the concise report."""
    disks = await get_disks_info()
    total = sum(disk["total"] for disk in disks)
    used = sum(disk["used"] for disk in disks)
    free = sum(disk["free"] for disk in disks)
    return {
        "total": total,
        "used": used,
        "free": free,
        "percent": (used / total * 100) if total else 0.0,
    }


async def get_cpu_usage() -> float:
    """Current CPU load. psutil needs two samples, hence the short interval."""
    return await asyncio.to_thread(psutil.cpu_percent, 0.5)


async def get_gpu_info() -> list[dict[str, str]]:
    """NVIDIA GPU stats via nvidia-smi. Returns [] when it is unavailable
    (no NVIDIA GPU or driver), so the report still works without a GPU section."""
    if shutil.which("nvidia-smi") is None:
        return []

    try:
        result = await process.run_async(
            ["nvidia-smi",
             "--query-gpu=name,memory.total,utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception:
        return []

    if result.returncode != 0:
        return []

    gpus = []
    for line in result.stdout.strip().splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 4:
            continue
        name, vram, load, temp = parts[:4]
        gpus.append({"name": name, "vram": vram, "load": load, "temp": temp})
    return gpus
