import platform
import getpass

import GPUtil
import psutil


async def get_system_info():

    system_info = {}
    system_info['Операционная система'] = platform.system()
    system_info['Имя компьютера'] = f"<b>{platform.node()}</b>"
    system_info['Пользователь'] = f"<b>{getpass.getuser()}</b>\n"
    system_info['Процессор'] = f"<code>{platform.processor()}</code>"
    system_info['Версия питона'] = f"<code>{platform.python_version()}</code>\n"

    return system_info


async def get_memory_info():
    memory_info = {}
    memory = psutil.virtual_memory()
    memory_info['Всего'] = f"{round(memory.total / (1024 ** 3), 2)} ГБ"
    memory_info['Доступно'] = f"{round(memory.available / (1024 ** 3), 2)} ГБ"
    memory_info['Использовано'] = f"{round(memory.used / (1024 ** 3), 2)} ГБ\n"
    return memory_info


async def get_disk_info():
    disk_info = []
    partitions = psutil.disk_partitions()
    for partition in partitions:
        usage = psutil.disk_usage(partition.mountpoint)
        disk_name = partition.mountpoint.split('/')[-1]
        disk_info.append({
            'Имя диска': disk_name,
            'Тип': partition.fstype,
            'Всего места': f"{round(usage.total / (1024 ** 3), 2)} ГБ",
            'Использовано места': f"{round(usage.used / (1024 ** 3), 2)} ГБ",
            'Доступно места': f"{round(usage.free / (1024 ** 3), 2)} ГБ\n"
        })
    return disk_info


async def get_gpu_info():
    gpu_info = {}
    gpus = GPUtil.getGPUs()
    for idx, gpu in enumerate(gpus, start=1):
        gpu_info[''] = {
            'Имя': f"<code>{gpu.name}</code>",
            'VRAM': f"{gpu.memoryTotal} МБ",
            'Использование GPU': f"{gpu.load * 100:.2f}%",
            'Температура GPU': f"{gpu.temperature} °C"
        }
    return gpu_info
