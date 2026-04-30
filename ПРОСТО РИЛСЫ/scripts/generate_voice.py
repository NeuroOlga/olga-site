"""
Генерация голосового сообщения (slide 9) через ElevenLabs + ffmpeg-постпроцесс
«записано на телефон в помещении».

Берёт voice_id, тексты, settings из config.voice_slide9.
API-ключ — из ENV `ELEVENLABS_API_KEY`.

Usage:
    ELEVENLABS_API_KEY=sk_... python scripts/generate_voice.py reels/01_banya
"""
from __future__ import annotations

import os
import subprocess
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import load_config, parse_reel_arg, resolve_path, reel_path


FFMPEG = os.path.expanduser("~/bin/ffmpeg")
API_BASE = "https://api.elevenlabs.io/v1/text-to-speech"


def tts(voice_id: str, text: str, model: str, settings: dict, fallback_text: str | None) -> bytes:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ERROR: задай ELEVENLABS_API_KEY в env")

    headers = {"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}
    url = f"{API_BASE}/{voice_id}"
    payload = {"text": text, "model_id": model, "voice_settings": settings}

    print(f"  TTS: voice={voice_id}, model={model}")
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code != 200 and fallback_text:
        print(f"  ! {model} failed ({r.status_code}), fallback eleven_multilingual_v2")
        payload = {"text": fallback_text, "model_id": "eleven_multilingual_v2", "voice_settings": settings}
        r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code != 200:
        sys.exit(f"ERROR {r.status_code}: {r.text[:300]}")
    return r.content


def postprocess(raw_path: str, final_path: str, atempo: float):
    """Эффект «записано на телефон»: bandpass + reverb + room noise + 32k mp3."""
    fc = (
        "anoisesrc=d=30:color=pink:amplitude=0.04,"
        "lowpass=f=1500,volume=0.20[bg];"
        f"[0:a]atempo={atempo},"
        "highpass=f=300,lowpass=f=3800,"
        "aecho=0.5:0.6:30:0.2,"
        "acompressor=threshold=-20dB:ratio=4:attack=5:release=120:makeup=3,"
        "volume=2.5[v];"
        "[v][bg]amix=inputs=2:duration=first:weights=1.0 0.5"
    )
    cmd = [
        FFMPEG, "-y",
        "-i", raw_path,
        "-filter_complex", fc,
        "-ac", "1", "-ar", "16000",
        "-c:a", "libmp3lame", "-b:a", "32k",
        final_path,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"ffmpeg error: {res.stderr[-1500:]}")


def main():
    reel_dir = parse_reel_arg(sys.argv)
    config = load_config(reel_dir)
    spec = config.get("voice_slide9")
    if not spec:
        sys.exit("ERROR: voice_slide9 не задан в config")

    final_out = resolve_path(config, spec["output"])
    final_out.parent.mkdir(parents=True, exist_ok=True)
    raw_out = reel_path(config, "_build", "voice_raw.mp3")
    raw_out.parent.mkdir(parents=True, exist_ok=True)

    audio = tts(
        voice_id=spec["voice_id"],
        text=spec.get("text_with_tags", spec.get("text_plain", "")),
        model=spec.get("model", "eleven_v3"),
        settings=spec.get("settings", {}),
        fallback_text=spec.get("text_plain"),
    )
    raw_out.write_bytes(audio)
    print(f"  raw: {raw_out.name} ({len(audio)} bytes)")

    print(f"  postprocess (atempo={spec.get('atempo', 2.0)}, phone effect)...")
    postprocess(str(raw_out), str(final_out), atempo=spec.get("atempo", 2.0))
    print(f"  ✓ {final_out}")
    raw_out.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
