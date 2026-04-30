"""
Кумулятивные WhatsApp-мокапы:
  - Шапка чата сверху с «Мартин Хозяин квартиры»
  - Каждый слайд показывает ВСЮ переписку до этого момента, новое сообщение — внизу
  - Старые сообщения видны сверху; если переписка длинная — старые обрезаются сверху,
    как при просмотре чата на телефоне
  - Фон обоев WhatsApp на весь экран
"""
import os, base64
from playwright.sync_api import sync_playwright

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(DIR)

PHOTO_BANYA = os.path.join(PROJECT, "slide1_real.png")
PHOTO_SELFIE = os.path.join(PROJECT, "slide5_real.png")
PHOTO_CROWD = os.path.join(PROJECT, "slide8_real.png")


def img_to_data_uri(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = path.split(".")[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  width: 1080px; height: 1920px;
  background: #000;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}
/* Чёрный холст 1080×1920. Контент чата живёт внутри .safe-zone,
   которая занимает середину экрана — Instagram-overlay'и (имя сверху,
   подпись/лайки снизу) ложатся на чёрные полосы и не закрывают чат. */
.slide {
  width: 1080px; height: 1920px;
  position: relative;
  background: #000;
}
/* Instagram safe-zone:
   Внутри чёрного 1080×1920 рендерим WhatsApp 1080×1170 как раньше,
   но дополнительно ужимаем через transform: scale, чтобы вокруг был
   запас под Instagram-overlay'и:
   - Сверху ~360px чёрного — ник IG, аватар, иконки.
   - Снизу ~600px чёрного — подпись, лайки, музыка, кнопки.
   - По бокам ~97px чёрного — на всякий случай.
   Содержимое чата (шрифт, аватары, пузыри) визуально уменьшается до 82%. */
.safe-zone {
  position: absolute;
  top: 360px;
  left: 0;
  width: 1080px;
  height: 1170px;
  background-color: #efeae2;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120"><g fill="%23d4ccbe" opacity="0.45"><circle cx="20" cy="20" r="3"/><circle cx="80" cy="50" r="3"/><circle cx="50" cy="90" r="3"/><circle cx="100" cy="100" r="3"/><circle cx="35" cy="60" r="2"/><circle cx="70" cy="25" r="2"/><circle cx="95" cy="75" r="2.5"/><path d="M30 25 Q35 20 40 25 T50 25" stroke="%23d4ccbe" stroke-width="2" fill="none"/><path d="M70 70 Q72 67 75 70 T82 70" stroke="%23d4ccbe" stroke-width="2" fill="none"/></g></svg>');
  overflow: hidden;
  transform: scale(0.82);
  transform-origin: top center;
}

/* Шапка чата прибита к верху safe-zone (т.е. фактически на 280px от верха кадра).
   Так имя «Мартин Хозяин квартиры» гарантированно не закрывается ник-оверлеем IG. */
.chat-header {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 150px;
  background: #f0f2f5;
  display: flex; align-items: center;
  padding: 0 32px;
  gap: 22px;
  border-bottom: 1px solid #e9e9e9;
  z-index: 10;
}
.chat-header .back { font-size: 60px; color: #54656f; line-height: 1; }
.chat-header .avatar {
  width: 90px; height: 90px; border-radius: 50%;
  background: #6b7c85;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 50px; font-weight: 600;
  flex-shrink: 0;
}
.chat-header .name-block { flex: 1; display: flex; flex-direction: column; }
.chat-header .name { font-size: 40px; font-weight: 600; color: #111; line-height: 1.1; }
.chat-header .status { font-size: 26px; color: #667781; margin-top: 4px; }
.chat-header .icons { display: flex; gap: 28px; align-items: center; color: #54656f; font-size: 48px; }

/* Контейнер сообщений: pin to bottom — старые уходят вверх, новые внизу.
   Координаты относительно .safe-zone, т.е. реально занимает y=430..1450 кадра. */
.chat-area {
  position: absolute;
  top: 150px; left: 0; right: 0; bottom: 0;
  padding: 24px 32px 24px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 16px;
  overflow: hidden;
}
.row { display: flex; }
.row.in  { justify-content: flex-start; }
.row.out { justify-content: flex-end; }

.bubble {
  max-width: 84%;
  min-width: 220px;
  padding: 22px 140px 30px 28px;
  border-radius: 24px;
  font-size: 46px;
  line-height: 1.32;
  color: #111;
  position: relative;
  box-shadow: 0 2px 3px rgba(0,0,0,0.10);
  word-wrap: break-word;
}
.bubble.in  { background:#ffffff; border-top-left-radius:8px; }
.bubble.out { background:#d9fdd3; border-top-right-radius:8px; }
.bubble .meta {
  position: absolute;
  bottom: 10px;
  right: 22px;
  font-size: 26px;
  display: inline-flex; align-items: center; gap: 4px;
}
.bubble.in  .meta { color:#8696a0; }
.bubble.out .meta { color:#667781; }
.checks { font-size: 30px; letter-spacing: -8px; line-height: 1; color:#53bdeb; margin-left:4px; }

/* media (с фото).
   max-height у фото уменьшен с 900 до 720 — иначе в safe-zone (~1020px высоты)
   фото+подпись+другие сообщения не влезают. */
.bubble.media { padding: 6px 6px 30px; max-width: 70%; }
.bubble.media .photo {
  display: block;
  width: 100%;
  max-height: 720px;
  object-fit: cover;
  border-radius: 18px;
}
.bubble.media .caption { padding: 14px 18px 2px; font-size: 38px; line-height: 1.3; }
.bubble.media .meta { bottom: 10px; right: 22px; }

/* voice (голосовое) */
.bubble.voice { padding: 22px 26px 30px; max-width: 86%; min-width: 580px; display: flex; align-items: center; gap: 18px; }
.voice-play {
  width: 64px; height: 64px; border-radius: 50%;
  background: transparent; color: #007aff;
  display: flex; align-items: center; justify-content: center;
  font-size: 44px; flex-shrink: 0;
}
.voice-wave { flex: 1; display: flex; align-items: center; gap: 4px; height: 50px; }
.voice-wave span { flex: 1; background: #007aff; border-radius: 2px; display: block; }
.voice-time { font-size: 30px; color: #667781; font-variant-numeric: tabular-nums; flex-shrink: 0; }
.voice-speed {
  background: #b9c6cc; color: #fff; font-weight:600; font-size: 28px;
  padding: 8px 18px; border-radius: 22px; flex-shrink: 0;
}
.voice-mic-btn {
  width: 64px; height: 64px; border-radius: 50%;
  background: #d2d8db; color: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; font-size: 32px;
}
.voice-header-label {
  font-size: 26px; color: #667781;
  margin-bottom: 6px;
  margin-left: 8px;
}

/* SOLO режим для слайда 9: голосовое сообщение по центру, увеличенное */
.chat-area.solo {
  justify-content: center;
}
.bubble.voice.solo {
  min-width: 820px;
  max-width: 92%;
  padding: 28px 30px 36px;
  gap: 22px;
}
.bubble.voice.solo .voice-play { width: 80px; height: 80px; font-size: 56px; }
.bubble.voice.solo .voice-wave { height: 70px; gap: 5px; }
.bubble.voice.solo .voice-time { font-size: 36px; }
.bubble.voice.solo .voice-speed { font-size: 32px; padding: 10px 22px; }
.bubble.voice.solo .voice-mic-btn { width: 80px; height: 80px; font-size: 40px; }

/* панель реакций — над пузырём */
.with-reactions { position: relative; }
.reactions-bar {
  position: absolute;
  top: -100px; left: 0;
  background: #ffffff;
  border-radius: 60px;
  padding: 12px 22px;
  display: inline-flex; gap: 16px; align-items: center;
  font-size: 50px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
  white-space: nowrap;
}
.reactions-bar .add {
  background: #f0f0f0; border-radius: 50%;
  width: 50px; height: 50px;
  display: flex; align-items: center; justify-content: center;
  font-size: 36px; color: #555;
}
"""

CHAT_HEADER = """
<div class="chat-header">
  <div class="back">‹</div>
  <div class="avatar">М</div>
  <div class="name-block">
    <div class="name">Мартин Хозяин квартиры</div>
    <div class="status">был(а) недавно</div>
  </div>
  <div class="icons"><span>📹</span><span>📞</span></div>
</div>
"""


VOICE_BARS = [30, 55, 80, 60, 45, 70, 90, 50, 35, 65, 80, 55, 40, 70, 60, 80, 45, 30, 55, 70, 90, 60, 40, 50]
VOICE_TOTAL_SEC = 22  # длительность голосового


def fmt_voice_time(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 60}:{s % 60:02d}"


def render_voice(msg, direction, time, progress: float = 0.0, solo: bool = False) -> str:
    """Рендер голосового сообщения с визуализацией прогресса.

    progress 0..1 — какая часть проиграна. Сыгранные бары становятся серыми,
    несыгранные — синие. Таймер показывает текущее время (если играет) или
    полную длительность (если ещё не запускалось).
    """
    n = len(VOICE_BARS)
    bars_html = []
    for i, h in enumerate(VOICE_BARS):
        played = (i + 0.5) / n <= progress
        color = '#8696a0' if played else '#007aff'
        bars_html.append(f'<span style="height:{h}%; background:{color}"></span>')
    bars = "".join(bars_html)

    # Если идёт проигрывание (progress > 0) — иконка паузы и текущее время.
    # Если ещё не запущено — иконка play и полное время.
    if progress > 0:
        play_icon = '❚❚'
        current_sec = progress * VOICE_TOTAL_SEC
        time_label = fmt_voice_time(current_sec)
    else:
        play_icon = '▶'
        time_label = msg.get("voice_dur", fmt_voice_time(VOICE_TOTAL_SEC))

    solo_class = ' solo' if solo else ''
    bubble_html = (
        f'<div class="bubble voice {direction}{solo_class}">'
        f'<button class="voice-play">{play_icon}</button>'
        f'<div class="voice-wave">{bars}</div>'
        f'<div class="voice-time">{time_label}</div>'
        f'<div class="voice-speed">1×</div>'
        f'<div class="voice-mic-btn">🎤</div>'
        + (f'<span class="meta">{time}</span>' if not solo else '')
        + '</div>'
    )

    if solo:
        # Соло режим — без ярлыка «Непрослушанное», без чекмарков, центрирован
        return f'<div class="row {direction}">{bubble_html}</div>'

    # В кумулятивном чате (если когда-нибудь использовать) — с ярлыком
    unread = '<div class="voice-header-label">Непрослушанное сообщение</div>' if msg.get("voice_unread") else ''
    return f'<div class="row {direction}"><div>{unread}{bubble_html}</div></div>'


def render_message(msg, photo_uris, is_latest=False):
    """Возвращает HTML одной строки чата (.row + .bubble).

    is_latest=True — это последнее сообщение текущего слайда. Только в этом
    случае показываем панель реакций (она транзитная — как при долгом нажатии
    в реальном WhatsApp), чтобы на последующих слайдах она не перекрывала
    предыдущие сообщения сверху.
    """
    direction = msg["dir"]
    time = msg.get("time", "")

    if msg.get("voice"):
        return render_voice(msg, direction, time, progress=msg.get("progress", 0.0), solo=msg.get("solo", False))

    if msg.get("photo"):
        photo_uri = photo_uris[msg["photo"]]
        text = msg.get("text", "")
        bubble = (
            f'<div class="bubble media {direction}">'
            f'<img class="photo" src="{photo_uri}">'
            f'{f"<div class=caption>{text}</div>" if text else ""}'
            f'<span class="meta">{time}'
            f'{"<span class=checks>✓✓</span>" if direction == "out" else ""}'
            f'</span></div>'
        )
        return f'<div class="row {direction}">{bubble}</div>'

    # Обычный текстовый пузырь.
    # Поле msg["reactions"] оставлено в данных для совместимости, но панель
    # реакций больше не рендерится — она перекрывала текст предыдущих сообщений.
    text = msg.get("text", "")
    bubble = (
        f'<div class="bubble {direction}">'
        f'{text}'
        f'<span class="meta">{time}'
        f'{"<span class=checks>✓✓</span>" if direction == "out" else ""}'
        f'</span></div>'
    )
    return f'<div class="row {direction}">{bubble}</div>'


def page(content, solo: bool = False):
    area_class = "chat-area solo" if solo else "chat-area"
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><style>{CSS}</style></head>
<body><div class="slide"><div class="safe-zone">{CHAT_HEADER}<div class="{area_class}">{content}</div></div></div></body></html>"""


# === Хронология чата ===
# id — короткий ключ, dir — out=Ольга, in=Мартин
THREAD = [
    {"id": "s2", "dir": "out",
     "text": "Мартин, привет!! 🌿 Мы тут с девочками русскую баню у вас сделали, заходи попариться!!",
     "time": "20:24", "photo": "BANYA"},

    {"id": "s3", "dir": "in", "text": "😳😳😳", "time": "20:29", "reactions": True},

    {"id": "s4", "dir": "in",
     "text": "Какую ещё баню?? Это ВАННАЯ КОМНАТА",
     "time": "20:30"},

    # Селфи Ольги (эскалация — она наслаждается процессом).
    # На самом слайде 5 показывается полноэкранным фото; в чате появляется
    # с этого момента и виден на слайдах 6, 7, 8, 9 как часть переписки.
    {"id": "s5_chat", "dir": "out", "text": "", "time": "20:31", "photo": "SELFIE"},

    {"id": "s6", "dir": "in",
     "text": "Завтра вы выезжаете из квартиры",
     "time": "20:33"},

    {"id": "s7", "dir": "in",
     "text": "Немедленно всё уберите и выключите пар, я еду",
     "time": "20:34"},

    {"id": "s8", "dir": "out",
     "text": "Хорошо, как скажешь 🙃 Мы тут ещё друзей позвали, им тоже понравилось!",
     "time": "20:34", "photo": "CROWD"},

    {"id": "s9", "dir": "in", "voice": True, "voice_dur": "0:22",
     "voice_unread": True, "time": "20:35"},
]

# Слайд → до какого id переписки показывать (включительно).
# Слайд 9 (голосовое) рендерится отдельно как соло-анимация (build_slide9_animated_frames).
SLIDE_OUTPUTS = [
    ("slide2_olga_invite", "s2"),
    ("slide3_martin_shock", "s3"),
    ("slide4_martin_question", "s4"),
    ("slide6_martin_threat", "s6"),
    ("slide7_martin_command", "s7"),
    ("slide8_olga_crowd", "s8"),
]

SLIDE9_FRAMES = 22  # 22 кадра по 1 fps = 22 секунды анимации проигрывания


def build_slide_html(name, last_id, photo_uris):
    # Берём все сообщения треда до last_id включительно
    msgs = []
    for m in THREAD:
        msgs.append(m)
        if m["id"] == last_id:
            break
    rendered_parts = []
    for i, m in enumerate(msgs):
        is_latest = (i == len(msgs) - 1)
        rendered_parts.append(render_message(m, photo_uris, is_latest=is_latest))
    rendered = "\n".join(rendered_parts)
    out = os.path.join(DIR, name + ".html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page(rendered))
    return out


def build_slide9_solo_html(progress: float, frame_idx: int) -> str:
    """HTML для одного кадра слайда 9 (соло, голосовое в центре с прогрессом)."""
    msg = {
        "id": "s9",
        "dir": "in",
        "voice": True,
        "voice_dur": "0:22",
        "progress": progress,
        "solo": True,
    }
    rendered = render_voice(msg, "in", "", progress=progress, solo=True)
    out = os.path.join(DIR, f"slide9_voice_f{frame_idx:02d}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page(rendered, solo=True))
    return out


def main():
    # удалить старые
    for f in os.listdir(DIR):
        if f.startswith("slide") and (f.endswith(".html") or f.endswith(".png") or f.endswith(".mp4")):
            os.remove(os.path.join(DIR, f))

    photo_uris = {
        "BANYA": img_to_data_uri(PHOTO_BANYA),
        "SELFIE": img_to_data_uri(PHOTO_SELFIE),
        "CROWD": img_to_data_uri(PHOTO_CROWD),
    }

    htmls = []
    for name, last_id in SLIDE_OUTPUTS:
        h = build_slide_html(name, last_id, photo_uris)
        htmls.append((name, h))
        print(f"  HTML: {name} (до {last_id})")

    # Слайд 9: 22 кадра анимированного проигрывания голосового (1 кадр/сек)
    slide9_htmls = []
    for i in range(SLIDE9_FRAMES):
        # progress в начале каждой секунды: 0/22 на 1-м кадре, 21/22 на 22-м
        progress = (i + 1) / SLIDE9_FRAMES
        h = build_slide9_solo_html(progress, i)
        slide9_htmls.append(h)
    print(f"  HTML: slide9_voice — {SLIDE9_FRAMES} кадров анимации")

    print("\nРендерю PNG...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)
        page_pw = ctx.new_page()
        # Обычные слайды
        for name, h in htmls:
            page_pw.goto("file://" + h)
            page_pw.wait_for_load_state("networkidle")
            png = h.replace(".html", ".png")
            page_pw.screenshot(path=png, full_page=False)
            print(f"  PNG: {os.path.basename(png)}")
        # Кадры слайда 9
        for h in slide9_htmls:
            page_pw.goto("file://" + h)
            page_pw.wait_for_load_state("networkidle")
            png = h.replace(".html", ".png")
            page_pw.screenshot(path=png, full_page=False)
        print(f"  PNG: slide9_voice_f00..f{SLIDE9_FRAMES-1:02d}")
        browser.close()

    # Собираем slide9_voice.mp4 из 22 кадров (1 кадр/сек) → 22 сек видео
    slide9_mp4 = os.path.join(DIR, "slide9_voice.mp4")
    pattern = os.path.join(DIR, "slide9_voice_f%02d.png")
    ffmpeg = os.path.expanduser("~/bin/ffmpeg")
    import subprocess
    cmd = [
        ffmpeg, "-y",
        "-framerate", "1",
        "-i", pattern,
        "-vf", "fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        slide9_mp4,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("ffmpeg slide9 error:", res.stderr[-1500:])
        raise SystemExit(1)
    print(f"  MP4: slide9_voice.mp4 ({SLIDE9_FRAMES} сек анимации)")

    print("\nГотово.")


if __name__ == "__main__":
    main()
