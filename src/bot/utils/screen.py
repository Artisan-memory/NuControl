import ctypes
from ctypes import wintypes

from PIL import ImageGrab

# Virtual desktop origin; negative when a monitor sits left of or above the primary one
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77

_MONITOR_ENUM_PROC = ctypes.WINFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
    ctypes.POINTER(wintypes.RECT), ctypes.c_double,
)

_dpi_ready = False


def _enable_dpi_awareness() -> None:
    """Capture true pixels; without this a scaled display comes back downscaled and blurry"""
    # Без этого на масштабе 125% скрин приходит мыльный
    global _dpi_ready
    if _dpi_ready:
        return
    try:
        # Per-monitor v2; older Windows builds lack it, so fall back to the system-wide flag
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass
    _dpi_ready = True


def monitor_rects() -> list[tuple[int, int, int, int]]:
    """Every monitor as (left, top, right, bottom) in virtual-desktop coordinates."""
    _enable_dpi_awareness()
    rects: list[tuple[int, int, int, int]] = []

    def collect(_monitor, _dc, rect_ptr, _data):
        rect = rect_ptr.contents
        rects.append((rect.left, rect.top, rect.right, rect.bottom))
        return 1

    ctypes.windll.user32.EnumDisplayMonitors(None, None, _MONITOR_ENUM_PROC(collect), 0)
    return rects


def grab_monitors() -> list:
    """One image per monitor, left to right - /screenshot

    Grabbed once and cropped, so the shots cannot drift apart in time.
    """
    _enable_dpi_awareness()
    desktop = ImageGrab.grab(all_screens=True)

    rects = monitor_rects()
    if len(rects) < 2:
        return [desktop]

    origin_x = ctypes.windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    origin_y = ctypes.windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN)

    shots = []
    for left, top, right, bottom in sorted(rects):
        box = (left - origin_x, top - origin_y, right - origin_x, bottom - origin_y)
        # Ignore a monitor the grab does not actually cover rather than crashing
        if box[0] < 0 or box[1] < 0 or box[2] > desktop.width or box[3] > desktop.height:
            continue
        shots.append(desktop.crop(box))
    return shots or [desktop]
