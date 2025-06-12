from datetime import datetime


class Timer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Timer, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'start_time'):  # Initialize only once
            self.start_time = None

    async def start(self):
        self.start_time = datetime.now()

    async def get_elapsed_time(self):
        if self.start_time is None:
            return "Timer hasn't started yet."

        elapsed = datetime.now() - self.start_time
        days, seconds = elapsed.days, elapsed.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        time_parts = []
        if days > 0:
            time_parts.append(f"{days}d")
        if hours > 0 or days > 0:  # Include hours if days are present or if hours are non-zero
            time_parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:  # Include minutes if hours or days are present or if minutes are non-zero
            time_parts.append(f"{minutes}m")
        time_parts.append(f"{seconds}s")

        return ", ".join(time_parts)
