"""
Генерация ЖИВОГО голосового сообщения для слайда 9 (Мартин).

Пайплайн:
  1. ElevenLabs eleven_v3 — голос с разнообразными эмоциями (теги [angry], [sigh], [shouting] и т.д.)
  2. Постпроцессинг через ffmpeg — добавляем эффект "записано на телефон":
     - lowpass ~6.5kHz (телефонный канал)
     - лёгкое room reverb (записано в помещении)
     - тихий фоновый шум комнаты + улицы
     - WhatsApp-компрессия (64kbps mp3)
"""
import os, sys, requests, subprocess, tempfile

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "PASTE_KEY_HERE")
PROJECT = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ"
RAW_OUT = os.path.join(PROJECT, "martin_voice_raw.mp3")
FINAL_OUT = os.path.join(PROJECT, "martin_voice_slide9.mp3")
FFMPEG = os.path.expanduser("~/bin/ffmpeg")

# === Голос ===
# Liam (молодой энергичный) — TX3LPaxmHKxFdv7VOQHJ
# Brian (взрослый серьёзный) — nPczCjzI2devNBz1zQrb
# Adam (глубокий) — pNInz6obpgDQGcFmaJgB
VOICE_ID = "pqHfZKP75CvOlQylNhV4"  # Bill — взрослый, авторитетный (хозяин 40+)

# Текст с междометиями "эээ" / "ммм" / "ну" / повторами — как реально думает и говорит
# взбешённый мужик. Эти "ну", "эээ", "ммм" между фразами + обрывы дают эффект живой речи.
TEXT = (
    "[scoffs] Ольга? Ольга, эээ... [breathes heavily] ну ты-ы серьёзно вообще?! "
    "[angry] Эээ, какая баня?! Какая баня в моей квартире?! "
    "Это, ммм... это ванная! Понимаешь? Просто ва́нная! "
    "[furious] Я уже... ну блин, я уже соседям снизу плачу за потоп, э-э, второй раз! "
    "[exhales sharply] Так, всё. Всё, всё, всё. Я в машине уже, я еду. "
    "[urgent] Двадцать минут — и я там, ясно? "
    "[threatening] И если там... ммм... если там кто-то ещё останется — "
    "[shouting] я тебя предупреждаю, я полицию вызываю, без шуток! "
    "[demanding] Ты слышишь меня вообще, Ольга?!"
)

TEXT_PLAIN = (
    "Ольга? Ольга, эээ... ну ты-ы серьёзно вообще?! "
    "Эээ, какая баня?! Какая баня в моей квартире?! "
    "Это, ммм... это ванная! Понимаешь? Просто ванная! "
    "Я уже... ну блин, я уже соседям снизу плачу за потоп, э-э, второй раз! "
    "Так, всё. Всё, всё, всё. Я в машине уже, я еду. "
    "Двадцать минут — и я там, ясно? "
    "И если там... ммм... если там кто-то ещё останется — "
    "я тебя предупреждаю, я полицию вызываю, без шуток! "
    "Ты слышишь меня вообще, Ольга?!"
)


def tts():
    if API_KEY == "PASTE_KEY_HERE":
        print("ERROR: задай ELEVENLABS_API_KEY в env", file=sys.stderr)
        sys.exit(1)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"}

    # Сначала eleven_v3 с тегами эмоций
    payload = {
        "text": TEXT,
        "model_id": "eleven_v3",
        "voice_settings": {
            "stability": 0.18,
            "similarity_boost": 0.75,
            "style": 0.92,
            "use_speaker_boost": True,
            "speed": 1.0,
        },
    }
    print(f"TTS: voice={VOICE_ID}, model=eleven_v3 (с тегами эмоций)")
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code != 200:
        print(f"  v3 failed ({r.status_code}: {r.text[:150]}), fallback на multilingual_v2")
        payload = {
            "text": TEXT_PLAIN,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.18,
                "similarity_boost": 0.75,
                "style": 0.95,
                "use_speaker_boost": True,
                "speed": 1.0,
            },
        }
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code != 200:
            print(f"ERROR {r.status_code}: {r.text}", file=sys.stderr)
            sys.exit(1)

    with open(RAW_OUT, "wb") as f:
        f.write(r.content)
    print(f"  raw saved: {RAW_OUT} ({len(r.content)} bytes)")


def postprocess():
    """
    Эффект "записано на телефон в помещении":
      - lowpass 6800 Hz (срезаем high-end как WhatsApp opus)
      - highpass 200 Hz (убираем гул)
      - aecho — лёгкое room reverb
      - мягкая компрессия
      - подмешиваем тихий фоновый шум (комнатный амбиент)
      - финал: 64kbps mp3 mono 22050 Hz (как WhatsApp голосовое)
    """
    # filter_complex:
    # 0:a — голос (ElevenLabs raw)
    # генерим розовый шум как фон комнаты, тихий
    # Реалистичный WhatsApp-голосовое-в-машине (упрощённая, рабочая цепочка):
    fc = (
        # фон: pink+brown noise с lowpass = шум машины, тихий
        "anoisesrc=d=30:color=pink:amplitude=0.04,"
        "lowpass=f=1500,"
        "volume=0.20[bg];"
        # голос: x2 ускорение + телефонный bandpass + лёгкое эхо + компрессия + БУСТ громкости
        "[0:a]atempo=2.0,"
        "highpass=f=300,lowpass=f=3800,"
        "aecho=0.5:0.6:30:0.2,"
        "acompressor=threshold=-20dB:ratio=4:attack=5:release=120:makeup=3,"
        "volume=2.5[v];"
        # микс голоса с фоном
        "[v][bg]amix=inputs=2:duration=first:weights=1.0 0.5"
    )
    cmd = [
        FFMPEG, "-y",
        "-i", RAW_OUT,
        "-filter_complex", fc,
        "-ac", "1",
        "-ar", "16000",            # как реальный WhatsApp opus
        "-c:a", "libmp3lame",
        "-b:a", "32k",             # низкое качество = "записал на телефон"
        FINAL_OUT,
    ]
    print(f"Постпроцессинг: lowpass+reverb+room noise+compression")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("ffmpeg error:", res.stderr[-1500:], file=sys.stderr)
        sys.exit(1)
    print(f"  ✓ Финал: {FINAL_OUT} ({os.path.getsize(FINAL_OUT)} bytes)")


def main():
    tts()
    postprocess()
    # удаляем raw, оставляем только финал
    try:
        os.remove(RAW_OUT)
    except:
        pass


if __name__ == "__main__":
    main()
