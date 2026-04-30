"""
Рендер WhatsApp-мокапов для рилса в формате `whatsapp_prank`.

Берёт config.json рилса, для каждого `slide_outputs[i]` строит
кумулятивный чат до `until_id`, рендерит HTML, делает PNG-скриншот.
Слайд 9 — отдельная соло-анимация голосового на 22 кадра, склеивается в mp4.

Usage:
    python scripts/build_mockups.py reels/01_banya
"""
from __future__ import annotations

import base64
import os
import subprocess
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import load_config, parse_reel_arg, resolve_path, reel_path


CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  width: 1080px; height: 1920px;
  background: #000;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}
.slide { width: 1080px; height: 1920px; position: relative; background: #000; }

/* Instagram safe-zone — см. шаблон whatsapp_prank.json */
.safe-zone {
  position: absolute;
  top: __SZ_TOP__px;
  left: 0;
  width: __SZ_W__px;
  height: __SZ_H__px;
  background-color: #efeae2;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120"><g fill="%23d4ccbe" opacity="0.45"><circle cx="20" cy="20" r="3"/><circle cx="80" cy="50" r="3"/><circle cx="50" cy="90" r="3"/><circle cx="100" cy="100" r="3"/><circle cx="35" cy="60" r="2"/><circle cx="70" cy="25" r="2"/><circle cx="95" cy="75" r="2.5"/><path d="M30 25 Q35 20 40 25 T50 25" stroke="%23d4ccbe" stroke-width="2" fill="none"/><path d="M70 70 Q72 67 75 70 T82 70" stroke="%23d4ccbe" stroke-width="2" fill="none"/></g></svg>');
  overflow: hidden;
  transform: scale(__SZ_SCALE__);
  transform-origin: top center;
}

.chat-header {
  position: absolute; top: 0; left: 0; right: 0;
  height: 150px; background: #f0f2f5;
  display: flex; align-items: center;
  padding: 0 32px; gap: 22px;
  border-bottom: 1px solid #e9e9e9; z-index: 10;
}
.chat-header .back { font-size: 60px; color: #54656f; line-height: 1; }
.chat-header .avatar {
  width: 90px; height: 90px; border-radius: 50%;
  background: __AVATAR_COLOR__;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 50px; font-weight: 600; flex-shrink: 0;
}
.chat-header .name-block { flex: 1; display: flex; flex-direction: column; }
.chat-header .name { font-size: 40px; font-weight: 600; color: #111; line-height: 1.1; }
.chat-header .status { font-size: 26px; color: #667781; margin-top: 4px; }
.chat-header .icons { display: flex; gap: 28px; align-items: center; color: #54656f; font-size: 48px; }

.chat-area {
  position: absolute;
  top: 150px; left: 0; right: 0; bottom: 0;
  padding: 24px 32px 24px;
  display: flex; flex-direction: column;
  justify-content: flex-end; gap: 16px;
  overflow: hidden;
}
.row { display: flex; }
.row.in  { justify-content: flex-start; }
.row.out { justify-content: flex-end; }
.bubble {
  max-width: 84%; min-width: 220px;
  padding: 22px 140px 30px 28px;
  border-radius: 24px;
  font-size: 46px; line-height: 1.32; color: #111;
  position: relative;
  box-shadow: 0 2px 3px rgba(0,0,0,0.10);
  word-wrap: break-word;
}
.bubble.in  { background:#ffffff; border-top-left-radius:8px; }
.bubble.out { background:#d9fdd3; border-top-right-radius:8px; }
.bubble .meta {
  position: absolute; bottom: 10px; right: 22px;
  font-size: 26px;
  display: inline-flex; align-items: center; gap: 4px;
}
.bubble.in  .meta { color:#8696a0; }
.bubble.out .meta { color:#667781; }
.checks { font-size: 30px; letter-spacing: -8px; line-height: 1; color:#53bdeb; margin-left:4px; }

.bubble.media { padding: 6px 6px 30px; max-width: 70%; }
.bubble.media .photo {
  display: block; width: 100%;
  max-height: 720px; object-fit: cover;
  border-radius: 18px;
}
.bubble.media .caption { padding: 14px 18px 2px; font-size: 38px; line-height: 1.3; }

.bubble.voice { padding: 22px 26px 30px; max-width: 86%; min-width: 580px; display: flex; align-items: center; gap: 18px; }
.voice-play { width: 64px; height: 64px; border-radius: 50%; background: transparent; color: #007aff;
  display: flex; align-items: center; justify-content: center; font-size: 44px; flex-shrink: 0; }
.voice-wave { flex: 1; display: flex; align-items: center; gap: 4px; height: 50px; }
.voice-wave span { flex: 1; background: #007aff; border-radius: 2px; display: block; }
.voice-time { font-size: 30px; color: #667781; font-variant-numeric: tabular-nums; flex-shrink: 0; }
.voice-speed { background: #b9c6cc; color: #fff; font-weight:600; font-size: 28px;
  padding: 8px 18px; border-radius: 22px; flex-shrink: 0; }
.voice-mic-btn { width: 64px; height: 64px; border-radius: 50%; background: #d2d8db; color: #fff;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 32px; }
.voice-header-label { font-size: 26px; color: #667781; margin-bottom: 6px; margin-left: 8px; }

.chat-area.solo { justify-content: center; }
.bubble.voice.solo { min-width: 820px; max-width: 92%; padding: 28px 30px 36px; gap: 22px; }
.bubble.voice.solo .voice-play { width: 80px; height: 80px; font-size: 56px; }
.bubble.voice.solo .voice-wave { height: 70px; gap: 5px; }
.bubble.voice.solo .voice-time { font-size: 36px; }
.bubble.voice.solo .voice-speed { font-size: 32px; padding: 10px 22px; }
.bubble.voice.solo .voice-mic-btn { width: 80px; height: 80px; font-size: 40px; }
"""


VOICE_BARS = [30, 55, 80, 60, 45, 70, 90, 50, 35, 65, 80, 55, 40, 70, 60, 80, 45, 30, 55, 70, 90, 60, 40, 50]


def img_to_data_uri(path: str) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = path.split(".")[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


def fmt_voice_time(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 60}:{s % 60:02d}"


def render_voice(msg, direction, time, total_sec=22, progress=0.0, solo=False) -> str:
    n = len(VOICE_BARS)
    bars = "".join(
        f'<span style="height:{h}%; background:{"#8696a0" if (i + 0.5) / n <= progress else "#007aff"}"></span>'
        for i, h in enumerate(VOICE_BARS)
    )
    if progress > 0:
        play_icon = "❚❚"
        time_label = fmt_voice_time(progress * total_sec)
    else:
        play_icon = "▶"
        time_label = msg.get("voice_dur", fmt_voice_time(total_sec))
    solo_class = " solo" if solo else ""
    bubble_html = (
        f'<div class="bubble voice {direction}{solo_class}">'
        f'<button class="voice-play">{play_icon}</button>'
        f'<div class="voice-wave">{bars}</div>'
        f'<div class="voice-time">{time_label}</div>'
        f'<div class="voice-speed">1×</div>'
        f'<div class="voice-mic-btn">🎤</div>'
        + (f'<span class="meta">{time}</span>' if not solo else "")
        + "</div>"
    )
    if solo:
        return f'<div class="row {direction}">{bubble_html}</div>'
    unread = '<div class="voice-header-label">Непрослушанное сообщение</div>' if msg.get("voice_unread") else ""
    return f'<div class="row {direction}"><div>{unread}{bubble_html}</div></div>'


def render_message(msg, photo_uris, voice_total_sec=22) -> str:
    direction = msg["dir"]
    time = msg.get("time", "")
    if msg.get("voice"):
        return render_voice(msg, direction, time, total_sec=voice_total_sec,
                            progress=msg.get("progress", 0.0), solo=msg.get("solo", False))
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
    text = msg.get("text", "")
    bubble = (
        f'<div class="bubble {direction}">'
        f'{text}'
        f'<span class="meta">{time}'
        f'{"<span class=checks>✓✓</span>" if direction == "out" else ""}'
        f'</span></div>'
    )
    return f'<div class="row {direction}">{bubble}</div>'


def build_css(safe_zone: dict, avatar_color: str) -> str:
    sz_w, sz_h = safe_zone.get("size", [1080, 1170])
    return (CSS
        .replace("__SZ_TOP__", str(safe_zone.get("top", 360)))
        .replace("__SZ_W__", str(sz_w))
        .replace("__SZ_H__", str(sz_h))
        .replace("__SZ_SCALE__", str(safe_zone.get("scale", 0.82)))
        .replace("__AVATAR_COLOR__", avatar_color)
    )


def build_chat_header(chat: dict) -> str:
    return f"""
<div class="chat-header">
  <div class="back">‹</div>
  <div class="avatar">{chat['recipient_avatar_letter']}</div>
  <div class="name-block">
    <div class="name">{chat['recipient_name']}</div>
    <div class="status">{chat.get('recipient_status', 'был(а) недавно')}</div>
  </div>
  <div class="icons"><span>📹</span><span>📞</span></div>
</div>
"""


def page(content: str, css: str, header: str, solo: bool = False) -> str:
    area_class = "chat-area solo" if solo else "chat-area"
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><style>{css}</style></head>
<body><div class="slide"><div class="safe-zone">{header}<div class="{area_class}">{content}</div></div></div></body></html>"""


def main():
    reel_dir = parse_reel_arg(sys.argv)
    config = load_config(reel_dir)

    mockups_dir = reel_path(config, "mockups")
    build_dir = reel_path(config, "_build")
    mockups_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    css = build_css(config.get("safe_zone", {}), config["chat"].get("recipient_avatar_color", "#6b7c85"))
    header = build_chat_header(config["chat"])

    photo_uris = {
        key: img_to_data_uri(str(resolve_path(config, p)))
        for key, p in config.get("photos", {}).items()
    }

    voice_total_sec = config.get("voice_slide9", {}).get("duration_sec", 22)
    thread = config["thread"]

    htmls = []
    for slide in config["slide_outputs"]:
        msgs = []
        for m in thread:
            msgs.append(m)
            if m["id"] == slide["until_id"]:
                break
        rendered = "\n".join(render_message(m, photo_uris, voice_total_sec) for m in msgs)
        out_html = build_dir / f"{slide['name']}.html"
        out_html.write_text(page(rendered, css, header), encoding="utf-8")
        htmls.append((slide["name"], out_html))
        print(f"  HTML: {slide['name']} (до {slide['until_id']})")

    # Слайд 9: соло-анимация
    slide9_frames = voice_total_sec
    slide9_htmls = []
    for i in range(slide9_frames):
        progress = (i + 1) / slide9_frames
        msg = {"id": "s9", "dir": "in", "voice": True, "progress": progress, "solo": True,
               "voice_dur": fmt_voice_time(voice_total_sec)}
        rendered = render_voice(msg, "in", "", total_sec=voice_total_sec, progress=progress, solo=True)
        out_html = build_dir / f"slide9_voice_f{i:02d}.html"
        out_html.write_text(page(rendered, css, header, solo=True), encoding="utf-8")
        slide9_htmls.append(out_html)
    print(f"  HTML: slide9_voice — {slide9_frames} кадров")

    print("\nРендерю PNG...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)
        pg = ctx.new_page()
        for name, h in htmls:
            pg.goto("file://" + str(h))
            pg.wait_for_load_state("networkidle")
            png = mockups_dir / f"{name}.png"
            pg.screenshot(path=str(png), full_page=False)
            print(f"  PNG: {png.name}")
        for h in slide9_htmls:
            pg.goto("file://" + str(h))
            pg.wait_for_load_state("networkidle")
            png = mockups_dir / (h.stem + ".png")
            pg.screenshot(path=str(png), full_page=False)
        print(f"  PNG: slide9_voice_f00..f{slide9_frames - 1:02d}")
        browser.close()

    # MP4 для слайда 9
    slide9_mp4 = mockups_dir / "slide9_voice.mp4"
    pattern = mockups_dir / "slide9_voice_f%02d.png"
    ffmpeg = os.path.expanduser("~/bin/ffmpeg")
    cmd = [
        ffmpeg, "-y",
        "-framerate", "1",
        "-i", str(pattern),
        "-vf", "fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        str(slide9_mp4),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("ffmpeg slide9 error:", res.stderr[-1500:])
        sys.exit(1)
    print(f"  MP4: slide9_voice.mp4 ({slide9_frames} сек)")
    print("\nГотово.")


if __name__ == "__main__":
    main()
