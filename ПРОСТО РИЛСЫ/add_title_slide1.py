"""
Накладывает на slide1_real.png хук-надпись в стиле референса:
  «ПРАНК НАД ХОЗЯИНОМ КВАРТИРЫ 😱»  (большой жирный белый текст с тенью)
  «(Не повторять!)»                  (поменьше, в скобках)

Сохраняет slide1_with_title.png.
"""
from PIL import Image, ImageDraw, ImageFont
import os

P = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ"

# --- Параметры надписи ---
LINE1 = "ПРАНК НАД"
LINE2 = "ХОЗЯИНОМ КВАРТИРЫ"
EMOJI = "😱"
LINE3 = "(Не повторять!)"

# Размеры подбираются под фактическое разрешение картинки в main().
# Базовые значения для 1080x1920; масштабируются пропорционально.
BASE_W = 1080
TITLE_SIZE_BASE = 72
SMALL_SIZE_BASE = 50
EMOJI_TARGET_BASE = 90
SAFE_MARGIN_FRAC = 0.08  # боковые отступы от краёв (как минимум)

# Шрифты macOS
# Заголовок: SF Pro (SFNS.ttf) — variable font, ставим Heavy для жирного капса как на референсе
FONT_TITLE_PATH = "/System/Library/Fonts/SFNS.ttf"
FONT_TITLE_VARIATION = b"Heavy"
# Подпись «(Не повторять!)»: SF Pro Regular
FONT_SMALL_PATH = "/System/Library/Fonts/SFNS.ttf"
FONT_SMALL_VARIATION = b"Semibold"

FONT_EMOJI = "/System/Library/Fonts/Apple Color Emoji.ttc"
EMOJI_NATIVE = 160  # Apple Color Emoji — допустимые размеры: 20, 32, 40, 48, 64, 96, 160

# Y-смещение блока надписи в долях от высоты картинки.
# Должно быть НИЖЕ лица Ольги — обычно лицо в верхней трети, текст ставим в середине/ниже.
TITLE_Y_FRAC = 0.55


def load_title_font(size: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT_TITLE_PATH, size)
    try:
        f.set_variation_by_name(FONT_TITLE_VARIATION)
    except Exception as e:
        print(f"WARN: could not set title variation: {e}")
    return f


def load_small_font(size: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT_SMALL_PATH, size)
    try:
        f.set_variation_by_name(FONT_SMALL_VARIATION)
    except Exception as e:
        print(f"WARN: could not set small variation: {e}")
    return f


def render_emoji(ch: str, target_px: int) -> Image.Image:
    """Рендерит цветной emoji на прозрачный фон и скейлит к target_px."""
    font = ImageFont.truetype(FONT_EMOJI, EMOJI_NATIVE)
    canvas = Image.new("RGBA", (EMOJI_NATIVE + 60, EMOJI_NATIVE + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    d.text((30, 0), ch, font=font, embedded_color=True)
    bbox = canvas.getbbox()
    if bbox:
        canvas = canvas.crop(bbox)
    scale = target_px / canvas.height
    new_size = (int(canvas.width * scale), int(canvas.height * scale))
    return canvas.resize(new_size, Image.LANCZOS)


def draw_text_with_shadow(draw, xy, text, font, fill=(255, 255, 255, 255),
                          shadow=(0, 0, 0, 200), offset=4):
    x, y = xy
    draw.text((x + offset, y + offset), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def main():
    src = os.path.join(P, "slide1_real.png")
    dst = os.path.join(P, "slide1_with_title.png")

    img = Image.open(src).convert("RGBA")
    W, H = img.size
    print(f"Image: {W}x{H}")

    scale = W / BASE_W
    TITLE_SIZE = int(TITLE_SIZE_BASE * scale)
    SMALL_SIZE = int(SMALL_SIZE_BASE * scale)
    EMOJI_TARGET = int(EMOJI_TARGET_BASE * scale)
    print(f"Scale: {scale:.2f}, title={TITLE_SIZE}, small={SMALL_SIZE}, emoji={EMOJI_TARGET}")

    font_title = load_title_font(TITLE_SIZE)
    font_small = load_small_font(SMALL_SIZE)

    # Авто-уменьшение, если самая длинная строка с emoji не помещается в безопасную ширину
    safe_w = int(W * (1 - 2 * SAFE_MARGIN_FRAC))
    tmp_draw = ImageDraw.Draw(img)

    def measure_line2(ts):
        f = load_title_font(ts)
        b = tmp_draw.textbbox((0, 0), LINE2, font=f)
        return (b[2] - b[0])

    while True:
        emoji_w_est = int(EMOJI_TARGET_BASE * scale * (TITLE_SIZE / int(TITLE_SIZE_BASE * scale)))
        line2_w = measure_line2(TITLE_SIZE) + int(18 * scale) + emoji_w_est
        if line2_w <= safe_w or TITLE_SIZE <= 40:
            break
        TITLE_SIZE = int(TITLE_SIZE * 0.95)
        SMALL_SIZE = int(SMALL_SIZE * 0.95)
        EMOJI_TARGET = int(EMOJI_TARGET * 0.95)

    print(f"Adjusted: title={TITLE_SIZE}, small={SMALL_SIZE}, emoji={EMOJI_TARGET}")
    font_title = load_title_font(TITLE_SIZE)
    font_small = load_small_font(SMALL_SIZE)

    emoji_img = render_emoji(EMOJI, EMOJI_TARGET)

    draw = ImageDraw.Draw(img)

    # Метрики
    def text_width(t, font):
        b = draw.textbbox((0, 0), t, font=font)
        return b[2] - b[0], b[3] - b[1]

    w1, h1 = text_width(LINE1, font_title)
    w2, h2 = text_width(LINE2, font_title)
    w3, h3 = text_width(LINE3, font_small)

    # Расположение блока: чуть ниже центра, как в референсе
    line_gap = int(TITLE_SIZE * 0.15)
    start_y = int(H * TITLE_Y_FRAC)
    sh = max(3, int(4 * scale))

    # line 1
    x1 = (W - w1) // 2
    y1 = start_y
    draw_text_with_shadow(draw, (x1, y1), LINE1, font_title, offset=sh)

    # line 2 с emoji справа
    gap_emoji = int(18 * scale)
    total_w2 = w2 + gap_emoji + emoji_img.width
    x2 = (W - total_w2) // 2
    y2 = y1 + h1 + line_gap
    draw_text_with_shadow(draw, (x2, y2), LINE2, font_title, offset=sh)
    # вертикально подровнять emoji к центру строки
    emoji_y = y2 + (h2 - emoji_img.height) // 2 - int(8 * scale)
    img.paste(emoji_img, (x2 + w2 + gap_emoji, emoji_y), emoji_img)

    # line 3 (поменьше, в скобках)
    x3 = (W - w3) // 2
    y3 = y2 + max(h2, emoji_img.height) + int(TITLE_SIZE * 0.5)
    draw_text_with_shadow(draw, (x3, y3), LINE3, font_small, offset=max(2, sh - 1))

    img.convert("RGB").save(dst, "PNG")
    print(f"Saved: {dst}")


if __name__ == "__main__":
    main()
