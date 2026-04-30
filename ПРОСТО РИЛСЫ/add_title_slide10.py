"""
Накладывает на slide10_real.png финальную надпись:
  «ПРАНК
   0 ИЗ 10»            (большой жирный белый текст SF Pro Heavy с тенью)
  «(Не повторять!)»    (поменьше)

Сохраняет slide10_with_title.png. Стиль/шрифт совпадает со слайдом 1
(см. add_title_slide1.py) — без emoji.
"""
from PIL import Image, ImageDraw, ImageFont
import os

P = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ"

# --- Параметры надписи ---
LINE1 = "ПРАНК"
LINE2 = "0 ИЗ 10"
LINE3 = "(Не повторять!)"

# Размеры подбираются под фактическое разрешение картинки в main().
BASE_W = 1080
TITLE_SIZE_BASE = 72
SMALL_SIZE_BASE = 50
SAFE_MARGIN_FRAC = 0.08

# Шрифты macOS — те же что на слайде 1 (SF Pro Heavy для заголовка)
FONT_TITLE_PATH = "/System/Library/Fonts/SFNS.ttf"
FONT_TITLE_VARIATION = b"Heavy"
FONT_SMALL_PATH = "/System/Library/Fonts/SFNS.ttf"
FONT_SMALL_VARIATION = b"Semibold"

# Y-смещение блока — ниже лица (~55% высоты)
TITLE_Y_FRAC = 0.55


def load_title_font(size: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT_TITLE_PATH, size)
    try:
        f.set_variation_by_name(FONT_TITLE_VARIATION)
    except Exception as e:
        print(f"WARN: title variation: {e}")
    return f


def load_small_font(size: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT_SMALL_PATH, size)
    try:
        f.set_variation_by_name(FONT_SMALL_VARIATION)
    except Exception as e:
        print(f"WARN: small variation: {e}")
    return f


def draw_text_with_shadow(draw, xy, text, font, fill=(255, 255, 255, 255),
                          shadow=(0, 0, 0, 200), offset=4):
    x, y = xy
    draw.text((x + offset, y + offset), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def main():
    src = os.path.join(P, "slide10_real.png")
    dst = os.path.join(P, "slide10_with_title.png")

    img = Image.open(src).convert("RGBA")
    W, H = img.size
    print(f"Image: {W}x{H}")

    scale = W / BASE_W
    TITLE_SIZE = int(TITLE_SIZE_BASE * scale)
    SMALL_SIZE = int(SMALL_SIZE_BASE * scale)
    print(f"Scale: {scale:.2f}, title={TITLE_SIZE}, small={SMALL_SIZE}")

    # Авто-уменьшение, если самая длинная строка не помещается
    safe_w = int(W * (1 - 2 * SAFE_MARGIN_FRAC))
    tmp_draw = ImageDraw.Draw(img)

    def measure(text, ts):
        f = load_title_font(ts)
        b = tmp_draw.textbbox((0, 0), text, font=f)
        return (b[2] - b[0])

    while True:
        widest = max(measure(LINE1, TITLE_SIZE), measure(LINE2, TITLE_SIZE))
        if widest <= safe_w or TITLE_SIZE <= 40:
            break
        TITLE_SIZE = int(TITLE_SIZE * 0.95)
        SMALL_SIZE = int(SMALL_SIZE * 0.95)

    print(f"Adjusted: title={TITLE_SIZE}, small={SMALL_SIZE}")
    font_title = load_title_font(TITLE_SIZE)
    font_small = load_small_font(SMALL_SIZE)

    draw = ImageDraw.Draw(img)

    def text_size(t, font):
        b = draw.textbbox((0, 0), t, font=font)
        return b[2] - b[0], b[3] - b[1]

    w1, h1 = text_size(LINE1, font_title)
    w2, h2 = text_size(LINE2, font_title)
    w3, h3 = text_size(LINE3, font_small)

    line_gap = int(TITLE_SIZE * 0.15)
    start_y = int(H * TITLE_Y_FRAC)
    sh = max(3, int(4 * scale))

    # line 1: "ПРАНК"
    x1 = (W - w1) // 2
    y1 = start_y
    draw_text_with_shadow(draw, (x1, y1), LINE1, font_title, offset=sh)

    # line 2: "0 ИЗ 10"
    x2 = (W - w2) // 2
    y2 = y1 + h1 + line_gap
    draw_text_with_shadow(draw, (x2, y2), LINE2, font_title, offset=sh)

    # line 3: "(Не повторять!)"
    x3 = (W - w3) // 2
    y3 = y2 + h2 + int(TITLE_SIZE * 0.5)
    draw_text_with_shadow(draw, (x3, y3), LINE3, font_small, offset=max(2, sh - 1))

    img.convert("RGB").save(dst, "PNG")
    print(f"Saved: {dst}")


if __name__ == "__main__":
    main()
