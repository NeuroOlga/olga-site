"""
Финальная сборка рилса: 10 слайдов с длительностями + музыка + голосовое.
Берёт пути и длительности из config.json.

Usage:
    python scripts/build_reel.py reels/01_banya
"""
from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import load_config, parse_reel_arg, resolve_path, reel_path, get_audio_duration


FFMPEG = os.path.expanduser("~/bin/ffmpeg")


def build_slide_paths(config: dict) -> list[tuple[str, float]]:
    """
    Возвращает список (path, duration) — 10 слайдов в правильном порядке.
    Имена ассетов и мокапов жёстко завязаны на формат whatsapp_prank.
    """
    durations = dict(config["build"]["slide_durations"])
    assets = lambda name: str(reel_path(config, "assets", name))
    mockups = lambda name: str(reel_path(config, "mockups", name))

    # Slide 9 длится РОВНО столько, сколько реальный голосовой файл (после atempo).
    # Иначе после окончания голоса остаётся тишина перед финалом — пользователь
    # это слышит как «затянулось». Если файла ещё нет — fallback на config.
    voice_path = resolve_path(config, config["voice_slide9"]["output"])
    voice_dur = get_audio_duration(voice_path)
    if voice_dur is not None:
        durations["slide9"] = round(voice_dur, 2)
        print(f"  slide9 = voice длительность: {durations['slide9']}s")

    # Маппинг имени слайда → файл. mockups/<until_id>.png — берём из slide_outputs.
    so_by_until = {s["until_id"]: s["name"] for s in config["slide_outputs"]}

    slides = [
        (assets("slide1_with_title.png"), durations["slide1"]),
        (mockups(f"{so_by_until['s2']}.png"), durations["slide2"]),
        (mockups(f"{so_by_until['s3']}.png"), durations["slide3"]),
        (mockups(f"{so_by_until['s4']}.png"), durations["slide4"]),
        (assets("slide5_real.png"), durations["slide5"]),
        (mockups(f"{so_by_until['s6']}.png"), durations["slide6"]),
        (mockups(f"{so_by_until['s7']}.png"), durations["slide7"]),
        (mockups(f"{so_by_until['s8']}.png"), durations["slide8"]),
        (mockups("slide9_voice.mp4"), durations["slide9"]),
        (assets("slide10_with_title.png"), durations["slide10"]),
    ]
    return slides


def build_video(slides, tmp_video):
    inputs = []
    for path, dur in slides:
        if path.lower().endswith(".mp4"):
            inputs += ["-i", path]
        else:
            inputs += ["-loop", "1", "-t", str(dur), "-i", path]

    parts = []
    for i in range(len(slides)):
        parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setsar=1,fps=30[v{i}]"
        )
    concat = "".join(f"[v{i}]" for i in range(len(slides)))
    parts.append(f"{concat}concat=n={len(slides)}:v=1:a=0[vout]")
    fc = ";".join(parts)

    cmd = [FFMPEG, "-y"] + inputs + [
        "-filter_complex", fc,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", "30",
        tmp_video,
    ]
    print("Step 1: silent video...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("ffmpeg video error:", res.stderr[-2000:])
        sys.exit(1)
    print(f"  ✓ {tmp_video}")


def build_audio_and_merge(config, slides, tmp_video, final_out):
    total = sum(d for _, d in slides)
    voice_start = sum(d for _, d in slides[:8])  # слайд 9 — индекс 8
    voice_end = voice_start + slides[8][1]

    music_path = str(resolve_path(config, config["build"]["music"]))
    voice_path = str(resolve_path(config, config["voice_slide9"]["output"]))
    duck = config["build"]["music_duck_volume"]
    normal = config["build"]["music_normal_volume"]
    voice_vol = config["build"]["voice_volume"]
    voice_start_ms = int(voice_start * 1000)

    fc = (
        f"[1:a]aloop=loop=-1:size=2e9,atrim=duration={total},"
        f"volume='if(between(t,{voice_start - 0.5},{voice_end + 0.5}),{duck},{normal})':eval=frame[music];"
        f"[2:a]adelay={voice_start_ms}|{voice_start_ms},volume={voice_vol}[voice];"
        f"[music][voice]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[aout]"
    )
    cmd = [
        FFMPEG, "-y",
        "-i", tmp_video,
        "-i", music_path,
        "-i", voice_path,
        "-filter_complex", fc,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        final_out,
    ]
    print(f"Step 2: mux audio (voice@{voice_start:.1f}s, ducking {normal}→{duck})...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("ffmpeg mux error:", res.stderr[-2000:])
        sys.exit(1)
    print(f"  ✓ {final_out}")
    os.remove(tmp_video)


def main():
    reel_dir = parse_reel_arg(sys.argv)
    config = load_config(reel_dir)

    slides = build_slide_paths(config)
    total = sum(d for _, d in slides)
    print(f"Reel: {config['name']}, total {total:.1f}s")

    final_out = str(reel_path(config, config["build"]["output"]))
    tmp_video = str(reel_path(config, "_build", "_tmp_video.mp4"))
    os.makedirs(os.path.dirname(tmp_video), exist_ok=True)

    build_video(slides, tmp_video)
    build_audio_and_merge(config, slides, tmp_video, final_out)

    sz = os.path.getsize(final_out) / 1024 / 1024
    print(f"\n🎬 Готово: {final_out} ({sz:.1f} MB, {total:.1f}s)")


if __name__ == "__main__":
    main()
