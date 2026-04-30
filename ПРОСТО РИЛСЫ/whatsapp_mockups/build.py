"""
Генерирует все 6 HTML-мокапов WhatsApp + рендерит их в PNG 1080x1920.
Накопительная переписка: каждый последующий слайд показывает историю + новое сообщение.
"""
import os, base64, sys
from playwright.sync_api import sync_playwright

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(DIR)

# Картинки для встраивания в WhatsApp пузыри (фото-сообщения)
PHOTO_BANYA = os.path.join(PROJECT, "slide1_real.png")             # отправляет Olga в slide 2
PHOTO_SELFIE = os.path.join(PROJECT, "slide5_real.png")            # отправляет Olga в slide 6
PHOTO_CROWD = os.path.join(PROJECT, "slide8_real.png")             # отправляет Olga в slide 9


def img_to_data_uri(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = path.split(".")[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


# ===================== МАКЕТ ХЭДЕРА И БАЗОВЫЙ HTML =====================

HEAD = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8">
<title>{title}</title><link rel="stylesheet" href="style.css"></head>
<body>
<div class="status-bar">
  <div class="left">{time}</div>
  <div class="right">
    <div class="signal-bars"><span></span><span></span><span></span><span></span></div>
    <span class="wifi-icon">📶</span>
    <div class="battery-icon"></div>
  </div>
</div>
<div class="chat-header">
  <div class="back-arrow">‹</div>
  <div class="unread-badge">12</div>
  <div class="avatar">M</div>
  <div class="chat-info">
    <div class="chat-name">Мартин Хозяин квартиры</div>
    <div class="chat-status">в сети</div>
  </div>
  <div class="header-icons">
    <svg class="icon-svg" viewBox="0 0 24 24"><path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/></svg>
    <svg class="icon-svg" viewBox="0 0 24 24"><path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56-.35-.12-.74-.03-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z"/></svg>
  </div>
</div>
<div class="chat-body">
  <div class="chat-inner">
  <div class="date-divider">сегодня</div>
"""

FOOT = """</div>
</div>
<div class="input-bar">
  <div class="input-icon">+</div>
  <div class="input-field">Сообщение</div>
  <div class="input-mic">🎤</div>
</div>
</body></html>
"""


# ===================== ВСПОМОГАТЕЛЬНЫЕ =====================

def text_bubble(direction, text, time, read=True):
    cls = "out" if direction == "out" else "in"
    checks = ""
    if direction == "out":
        cls_check = "read" if read else "sent"
        checks = f'<span class="checks {cls_check}">✓✓</span>'
    return f'<div class="bubble {cls}">{text}<span class="meta">{time}{checks}</span></div>'


def media_bubble(direction, photo_data_uri, caption, time, read=True):
    cls = "out" if direction == "out" else "in"
    checks = ""
    if direction == "out":
        cls_check = "read" if read else "sent"
        checks = f'<span class="checks {cls_check}">✓✓</span>'
    cap = f'<div class="caption">{caption}</div>' if caption else ""
    return (
        f'<div class="bubble media {cls}">'
        f'<img class="photo" src="{photo_data_uri}">'
        f'{cap}'
        f'<span class="meta">{time}{checks}</span>'
        f'</div>'
    )


def voice_bubble(direction, duration, time, played=False):
    cls = "out" if direction == "out" else "in"
    bars = "".join(
        f'<span style="height: {h}%"></span>'
        for h in [30, 55, 80, 60, 45, 70, 90, 50, 35, 65, 80, 55, 40, 70, 60, 80, 45, 30, 55, 70, 90, 60, 40, 50]
    )
    checks = ""
    if direction == "out":
        checks = '<span class="checks read">✓✓</span>'
    return (
        f'<div class="bubble voice {cls}">'
        f'  <button class="voice-play">▶</button>'
        f'  <div class="voice-avatar"><div class="mic-badge">🎤</div></div>'
        f'  <div class="voice-waveform" style="display:flex;align-items:center;height:40px;">{bars}</div>'
        f'  <span class="voice-duration">{duration}</span>'
        f'  <span class="meta">{time}{checks}</span>'
        f'</div>'
    )


# ===================== ПЕРЕПИСКА (накопительная) =====================
# Каждый ключ = слайд, значение = (статус-бар-время, [реплики...])

PHOTO_BANYA_URI = img_to_data_uri(PHOTO_BANYA)
PHOTO_SELFIE_URI = img_to_data_uri(PHOTO_SELFIE)
PHOTO_CROWD_URI = img_to_data_uri(PHOTO_CROWD)


def slide2_msgs():
    return [
        media_bubble("out", PHOTO_BANYA_URI, "Мартин, привет!! 🌿 Мы тут с девочками русскую баню у вас сделали, заходи попариться!!", "14:20", read=False),
    ]

def slide3_msgs():
    return slide2_msgs() + [
        text_bubble("in", "😳😳😳", "14:21"),
    ]

def slide4_msgs():
    return slide3_msgs() + [
        text_bubble("in", "Какую ещё баню?? Это ВАННАЯ КОМНАТА", "14:23"),
    ]

def slide6_msgs():
    return slide4_msgs() + [
        media_bubble("out", PHOTO_SELFIE_URI, "Уже так классно, всё работает 😊 Приходи скорее, веник второй есть!", "14:25", read=True),
        text_bubble("in", "Вы серьёзно сейчас??? Завтра освобождаете квартиру!!!", "14:25"),
    ]

def slide7_msgs():
    return slide6_msgs() + [
        text_bubble("in", "Немедленно всё уберите и выключите пар, я еду", "14:26"),
    ]

def slide9_msgs():
    return slide7_msgs() + [
        media_bubble("out", PHOTO_CROWD_URI, "Хорошо, как скажешь 🙃 Мы тут ещё друзей позвали, им тоже понравилось!", "14:31", read=True),
        voice_bubble("in", "0:22", "14:32", played=False),
    ]


SLIDES = {
    "slide2_olga_invite":   ("14:20", slide2_msgs),
    "slide3_martin_shock":  ("14:21", slide3_msgs),
    "slide4_martin_question": ("14:23", slide4_msgs),
    "slide6_martin_threat": ("14:25", slide6_msgs),
    "slide7_martin_command": ("14:26", slide7_msgs),
    "slide9_voice":         ("14:32", slide9_msgs),
}


def render_html(name, status_time, msgs_fn):
    html = HEAD.format(title=name, time=status_time)
    for m in msgs_fn():
        html += "  " + m + "\n"
    html += FOOT
    out = os.path.join(DIR, name + ".html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    return out


def main():
    htmls = []
    for name, (st, fn) in SLIDES.items():
        path = render_html(name, st, fn)
        htmls.append(path)
        print(f"  HTML: {os.path.basename(path)}")

    print("\nРендерю PNG...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)
        page = ctx.new_page()
        for h in htmls:
            page.goto("file://" + h)
            page.wait_for_load_state("networkidle")
            png = h.replace(".html", ".png")
            page.screenshot(path=png, full_page=False)
            print(f"  PNG: {os.path.basename(png)}")
        browser.close()
    print("\nГотово.")


if __name__ == "__main__":
    main()
