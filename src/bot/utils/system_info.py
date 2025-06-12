import psutil

class SystemInfo:
    @staticmethod
    async def get_memory_info():
        memory = psutil.virtual_memory()
        return {
            'Total': f"{round(memory.total / (1024 ** 3), 2)} GB",
            'Available': f"{round(memory.available / (1024 ** 3), 2)} GB",
            'Used': f"{round(memory.used / (1024 ** 3), 2)} GB",
            'Used Percentage': f"{memory.percent}%"
        }

    @staticmethod
    async def get_disk_info():
        total_space = 0
        used_space = 0
        free_space = 0
        for partition in psutil.disk_partitions():
            usage = psutil.disk_usage(partition.mountpoint)
            total_space += usage.total
            used_space += usage.used
            free_space += usage.free

        return {
            'Total Space': f"{round(total_space / (1024 ** 3), 2)} GB",
            'Used Space': f"{round(used_space / (1024 ** 3), 2)} GB",
            'Free Space': f"{round(free_space / (1024 ** 3), 2)} GB",
            'Used Percentage': f"{(used_space / total_space) * 100:.2f}%"
        }

    @staticmethod
    async def get_cpu_info():
        # To get accurate CPU usage, we need to take multiple readings over a short period,
        # but I don't recommend use this
        cpu_usage = psutil.cpu_percent(interval=1)
        return {
            'CPU Usage': f"{cpu_usage}%"
        }

    async def get_system_info(self):
        memory_info = await self.get_memory_info()
        disk_info = await self.get_disk_info()
        cpu_info = await self.get_cpu_info()

        return {
            'Memory': memory_info,
            'Disk': disk_info,
            'CPU': cpu_info
        }
