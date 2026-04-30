"""
Накладывает белые жирные SF Pro Heavy надписи на хук-фото (slide 1)
и финал-фото (slide 10). Берёт пути и тексты из config.json.

Usage:
    python scripts/add_titles.py reels/01_banya
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import load_config, parse_reel_arg, resolve_path


FONT_PATH = "/System/Library/Fonts/SFNS.ttf"
FONT_TITLE_VAR = b"Heavy"
FONT_SMALL_VAR = b"Semibold"
FONT_EMOJI = "/System/Library/Fonts/Apple Color Emoji.ttc"
EMOJI_NATIVE = 160
BASE_W = 1080
SAFE_MARGIN_FRAC = 0.08


def load_font(size: int, variation: bytes) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT_PATH, size)
    try:
        f.set_variation_by_name(variation)
    except Exception as e:
        print(f"  WARN: variation {variation!r}: {e}")
    return f


def render_emoji(ch: str, target_px: int) -> Image.Image:
    font = ImageFont.truetype(FONT_EMOJI, EMOJI_NATIVE)
    canvas = Image.new("RGBA", (EMOJI_NATIVE + 60, EMOJI_NATIVE + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    d.text((30, 0), ch, font=font, embedded_color=True)
    bbox = canvas.getbbox()
    if bbox:
        canvas = canvas.crop(bbox)
    scale = target_px / canvas.height
    return canvas.resize((int(canvas.width * scale), int(canvas.height * scale)), Image.LANCZOS)


def draw_text_with_shadow(draw, xy, text, font, fill=(255, 255, 255, 255),
                          shadow=(0, 0, 0, 200), offset=4):
    x, y = xy
    draw.text((x + offset, y + offset), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def add_title(src_path: Path, dst_path: Path, lines: list[str], subtitle: str,
              y_frac: float, title_size_base: int, small_size_base: int,
              emoji: str | None = None, emoji_size_base: int = 90):
    """
    Накладывает 2 строки заголовка (`lines`) + подпись (`subtitle`) внизу.
    Если emoji задан — добавляется справа от ВТОРОЙ строки.
    """
    img = Image.open(src_path).convert("RGBA")
    W, H = img.size
    print(f"  {src_path.name}: {W}x{H}")

    scale = W / BASE_W
    title_size = int(title_size_base * scale)
    small_size = int(small_size_base * scale)
    emoji_size = int(emoji_size_base * scale) if emoji else 0

    # Авто-уменьшение если самая длинная строка не помещается
    safe_w = int(W * (1 - 2 * SAFE_MARGIN_FRAC))
    tmp_draw = ImageDraw.Draw(img)

    def line_width(text: str, ts: int, with_emoji: bool = False) -> int:
        f = load_font(ts, FONT_TITLE_VAR)
        b = tmp_draw.textbbox((0, 0), text, font=f)
        w = b[2] - b[0]
        if with_emoji:
            w += int(18 * scale) + emoji_size
        return w

    while True:
        widest = max(
            line_width(lines[0], title_size, False),
            line_width(lines[-1], title_size, with_emoji=bool(emoji)),
        )
        if widest <= safe_w or title_size <= 40:
            break
        title_size = int(title_size * 0.95)
        small_size = int(small_size * 0.95)
        emoji_size = int(emoji_size * 0.95) if emoji else 0

    font_title = load_font(title_size, FONT_TITLE_VAR)
    font_small = load_font(small_size, FONT_SMALL_VAR)
    emoji_img = render_emoji(emoji, emoji_size) if emoji else None

    draw = ImageDraw.Draw(img)
    sh = max(3, int(4 * scale))
    line_gap = int(title_size * 0.15)
    start_y = int(H * y_frac)

    def text_size(t: str, font) -> tuple[int, int]:
        b = draw.textbbox((0, 0), t, font=font)
        return b[2] - b[0], b[3] - b[1]

    cur_y = start_y
    for i, line in enumerate(lines):
        is_last = (i == len(lines) - 1)
        w, h = text_size(line, font_title)
        if is_last and emoji_img is not None:
            gap_emoji = int(18 * scale)
            total_w = w + gap_emoji + emoji_img.width
            x = (W - total_w) // 2
            draw_text_with_shadow(draw, (x, cur_y), line, font_title, offset=sh)
            emoji_y = cur_y + (h - emoji_img.height) // 2 - int(8 * scale)
            img.paste(emoji_img, (x + w + gap_emoji, emoji_y), emoji_img)
            row_h = max(h, emoji_img.height)
        else:
            x = (W - w) // 2
            draw_text_with_shadow(draw, (x, cur_y), line, font_title, offset=sh)
            row_h = h
        cur_y += row_h + line_gap

    if subtitle:
        w3, h3 = text_size(subtitle, font_small)
        x3 = (W - w3) // 2
        y3 = cur_y + int(title_size * 0.35)
        draw_text_with_shadow(draw, (x3, y3), subtitle, font_small, offset=max(2, sh - 1))

    img.convert("RGB").save(dst_path, "PNG")
    print(f"  saved: {dst_path.name}")


def main():
    reel_dir = parse_reel_arg(sys.argv)
    config = load_config(reel_dir)

    for key in ("title_slide_1", "title_slide_10"):
        spec = config.get(key)
        if not spec:
            print(f"  пропуск {key}: не задан в config")
            continue
        src = resolve_path(config, spec["source"])
        dst = resolve_path(config, spec["output"])
        if not src.exists():
            print(f"  ! пропуск {key}: source не существует: {src}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        add_title(
            src, dst,
            lines=spec["lines"],
            subtitle=spec.get("subtitle", ""),
            y_frac=spec.get("y_frac", 0.55),
            title_size_base=spec.get("title_size_base", 72),
            small_size_base=spec.get("small_size_base", 50),
            emoji=spec.get("emoji"),
            emoji_size_base=spec.get("emoji_size_base", 90),
        )
    print("\nГотово.")


if __name__ == "__main__":
    main()
