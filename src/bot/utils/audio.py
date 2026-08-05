import asyncio
import winsound


def _play_blocking(path: str) -> None:
    try:
        import sounddevice
        import soundfile
    except ImportError:
        # Без них остаётся только winsound, а он умеет один wav
        winsound.PlaySound(path, winsound.SND_FILENAME)
        return

    data, samplerate = soundfile.read(path, dtype="float32")
    sounddevice.play(data, samplerate)
    sounddevice.wait()


async def play(path: str) -> None:
    """Проигрывает файл в текущее устройство вывода - колонки, наушники, что стоит по умолчанию"""
    await asyncio.to_thread(_play_blocking, path)
