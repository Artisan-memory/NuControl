"""Renders the /check report as a PNG card. Returns None on any failure so the
caller falls back to the text report - a missing font must never break /check."""

import os

from PIL import Image, ImageDraw, ImageFont

from src.config import TMP_DIR

WIDTH = 720
PADDING = 28
# Tall enough for label, bar and detail line plus the gap between two cards
ROW_HEIGHT = 80
HEADER_HEIGHT = 96
BAR_HEIGHT = 16
BAR_RADIUS = 8

BACKGROUND = (24, 26, 32)
CARD = (33, 36, 44)
TEXT = (236, 238, 243)
MUTED = (146, 152, 166)
TRACK = (52, 56, 68)

# Зелёный до 70%, жёлтый до 90%, дальше красный - чтобы по цвету всё было понятно
LEVELS = ((70, (86, 190, 122)), (90, (226, 176, 78)), (101, (224, 100, 100)))

FONT_CANDIDATES = ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf")
BOLD_CANDIDATES = ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf")


def _load_font(candidates: tuple[str, ...], size: int):
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _bar_color(percent: float) -> tuple[int, int, int]:
    for limit, color in LEVELS:
        if percent < limit:
            return color
    return LEVELS[-1][1]


def _draw_meter(draw, x: int, y: int, width: int, percent: float) -> None:
    draw.rounded_rectangle((x, y, x + width, y + BAR_HEIGHT), BAR_RADIUS, fill=TRACK)
    filled = int(width * min(max(percent, 0), 100) / 100)
    if filled > 0:
        draw.rounded_rectangle(
            (x, y, x + max(filled, BAR_HEIGHT), y + BAR_HEIGHT),
            BAR_RADIUS, fill=_bar_color(percent),
        )


def render_report(title: str, subtitle: str, meters: list[dict]) -> str | None:
    """Draws the card and returns its path. Each meter carries a label, a detail line
    and a percent."""
    try:
        height = HEADER_HEIGHT + len(meters) * ROW_HEIGHT + PADDING
        image = Image.new("RGB", (WIDTH, height), BACKGROUND)
        draw = ImageDraw.Draw(image)

        title_font = _load_font(BOLD_CANDIDATES, 26)
        label_font = _load_font(BOLD_CANDIDATES, 17)
        detail_font = _load_font(FONT_CANDIDATES, 15)

        draw.text((PADDING, PADDING), title, font=title_font, fill=TEXT)
        draw.text((PADDING, PADDING + 34), subtitle, font=detail_font, fill=MUTED)

        inner_width = WIDTH - PADDING * 2
        y = HEADER_HEIGHT
        for meter in meters:
            draw.rounded_rectangle((PADDING - 10, y - 10, WIDTH - PADDING + 10, y + ROW_HEIGHT - 14),
                                   12, fill=CARD)
            draw.text((PADDING, y), meter["label"], font=label_font, fill=TEXT)

            percent_text = f"{meter['percent']:.0f}%"
            percent_width = draw.textlength(percent_text, font=label_font)
            draw.text((WIDTH - PADDING - percent_width, y), percent_text,
                      font=label_font, fill=_bar_color(meter["percent"]))

            _draw_meter(draw, PADDING, y + 24, inner_width, meter["percent"])
            draw.text((PADDING, y + 44), meter["detail"], font=detail_font, fill=MUTED)
            y += ROW_HEIGHT

        os.makedirs(TMP_DIR, exist_ok=True)
        path = os.path.join(TMP_DIR, "check_report.png")
        image.save(path)
        return path
    except Exception:
        return None
