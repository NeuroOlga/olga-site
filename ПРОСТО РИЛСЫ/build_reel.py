"""
Финальная сборка рилса про баню — 10 слайдов с длительностями + аудио (музыка + голосовое на слайде 9).
Output: banya_reel.mp4 (1080x1920, 30 fps, H264, AAC)
"""
import subprocess, os

P = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ"
M = os.path.join(P, "whatsapp_mockups")
FFMPEG = os.path.expanduser("~/bin/ffmpeg")

# (путь до картинки, длительность в секундах)
SLIDES = [
    (os.path.join(P, "slide1_with_title.png"),           1.5),
    (os.path.join(M, "slide2_olga_invite.png"),          2.0),
    (os.path.join(M, "slide3_martin_shock.png"),         1.0),
    (os.path.join(M, "slide4_martin_question.png"),      1.8),
    (os.path.join(P, "slide5_real.png"),                 1.8),
    (os.path.join(M, "slide6_martin_threat.png"),        1.8),
    (os.path.join(M, "slide7_martin_command.png"),       1.8),
    (os.path.join(M, "slide8_olga_crowd.png"),           2.5),
    (os.path.join(M, "slide9_voice.png"),                22.0),
    (os.path.join(P, "slide10_real.png"),                2.5),
]
TOTAL = sum(d for _, d in SLIDES)
print(f"Total reel duration: {TOTAL:.1f}s")

# Время начала слайда 9 — для синхронизации голосового
SLIDE9_START = sum(d for _, d in SLIDES[:8])
print(f"Slide 9 starts at: {SLIDE9_START:.1f}s")

VOICE = os.path.join(P, "martin_voice_slide9.mp3")
MUSIC = os.path.join(P, "background_music.mp3")
HOOKS_OUT = os.path.join(P, "banya_reel.mp4")
TMP_VIDEO = os.path.join(P, "_tmp_video.mp4")


def build_video():
    # 1) Создаём видео из изображений: каждое -loop 1 -t <длительность>
    # Используем concat через filter_complex
    inputs = []
    for path, dur in SLIDES:
        inputs += ["-loop", "1", "-t", str(dur), "-i", path]

    # filter_complex: scale & pad each image to 1080x1920, set fps, then concat
    filter_parts = []
    for i in range(len(SLIDES)):
        # все изображения и так 1080x1920, но на всякий случай scale+pad
        filter_parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setsar=1,fps=30[v{i}]"
        )
    concat_inputs = "".join(f"[v{i}]" for i in range(len(SLIDES)))
    filter_parts.append(f"{concat_inputs}concat=n={len(SLIDES)}:v=1:a=0[vout]")
    filter_complex = ";".join(filter_parts)

    cmd = [FFMPEG, "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        TMP_VIDEO,
    ]
    print("Step 1: rendering silent video...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("ffmpeg video error:", res.stderr[-2000:])
        raise SystemExit(1)
    print(f"  ✓ {TMP_VIDEO}")


def build_audio_and_merge():
    # 2) Аудио: фоновая музыка зацикленная под TOTAL длительность,
    #    голосовое начинается на SLIDE9_START, музыка на слайде 9 приглушается до 0.30
    # Filter:
    #   [1:a] музыка → loop, цикл, обрезать по TOTAL
    #   [2:a] voice → задержка SLIDE9_START*1000 ms через adelay
    #   smooth volume duck on music during voice (через volume expression)

    # Строим filter_complex:
    #   - music: aloop, atrim до TOTAL, потом volume duck во время голоса
    #   - voice: adelay для синхронизации с слайдом 9
    #   - amix
    voice_start_ms = int(SLIDE9_START * 1000)
    voice_end = SLIDE9_START + 22.0  # длительность голосового ~22 сек

    fc = (
        # музыка: цикл и обрезка под общую длительность
        f"[1:a]aloop=loop=-1:size=2e9,atrim=duration={TOTAL},"
        # ducking: volume по времени — тише когда играет голос
        f"volume='if(between(t,{SLIDE9_START - 0.5},{voice_end + 0.5}),0.30,0.85)':eval=frame[music];"
        # голос: задержка до начала слайда 9
        f"[2:a]adelay={voice_start_ms}|{voice_start_ms},volume=1.4[voice];"
        # микс
        f"[music][voice]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[aout]"
    )
    cmd = [
        FFMPEG, "-y",
        "-i", TMP_VIDEO,
        "-i", MUSIC,
        "-i", VOICE,
        "-filter_complex", fc,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        HOOKS_OUT,
    ]
    print("Step 2: muxing audio (music + voice with ducking)...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("ffmpeg mux error:", res.stderr[-2000:])
        raise SystemExit(1)
    print(f"  ✓ {HOOKS_OUT}")
    os.remove(TMP_VIDEO)


def main():
    build_video()
    build_audio_and_merge()
    sz = os.path.getsize(HOOKS_OUT) / 1024 / 1024
    print(f"\n🎬 Готово: {HOOKS_OUT} ({sz:.1f} MB, {TOTAL:.1f}s)")


if __name__ == "__main__":
    main()
