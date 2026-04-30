"""
Создаёт скелет нового рилса в reels/<NN_name>/ из шаблона.

Что делает:
- mkdir reels/<NN_name>/{refs,assets,mockups,voice,_build}
- копирует config.example.json из templates → reels/<NN_name>/config.json (с подстановкой имени)
- печатает следующие шаги

Usage:
    python scripts/new_reel.py 02_lysaya whatsapp_prank
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import REELS_DIR, TEMPLATES_DIR


SKELETONS = {
    "whatsapp_prank": {
        "format": "whatsapp_prank",
        "title_slide_1": {
            "lines": ["ПРАНК НАД", "ПОЛУЧАТЕЛЕМ"],
            "emoji": "😱",
            "source": "assets/slide1_real.png",
            "output": "assets/slide1_with_title.png"
        },
        "title_slide_10": {
            "source": "assets/slide10_real.png",
            "output": "assets/slide10_with_title.png"
        },
        "chat": {
            "recipient_name": "Получатель",
            "recipient_avatar_letter": "?"
        },
        "thread": [
            {"id": "s2", "dir": "out", "text": "...", "time": "20:24", "photo": "HOOK_PHOTO"},
            {"id": "s3", "dir": "in", "text": "😳😳😳", "time": "20:29"},
            {"id": "s4", "dir": "in", "text": "...", "time": "20:30"},
            {"id": "s5_chat", "dir": "out", "text": "", "time": "20:31", "photo": "SELFIE"},
            {"id": "s6", "dir": "in", "text": "...", "time": "20:33"},
            {"id": "s7", "dir": "in", "text": "...", "time": "20:34"},
            {"id": "s8", "dir": "out", "text": "...", "time": "20:34", "photo": "ESCALATION"},
            {"id": "s9", "dir": "in", "voice": True, "voice_dur": "0:22", "voice_unread": True, "time": "20:35"}
        ],
        "photos": {
            "HOOK_PHOTO": "assets/slide1_real.png",
            "SELFIE": "assets/slide5_real.png",
            "ESCALATION": "assets/slide8_real.png"
        },
        "slide_outputs": [
            {"name": "slide2", "until_id": "s2"},
            {"name": "slide3", "until_id": "s3"},
            {"name": "slide4", "until_id": "s4"},
            {"name": "slide6", "until_id": "s6"},
            {"name": "slide7", "until_id": "s7"},
            {"name": "slide8", "until_id": "s8"}
        ],
        "voice_slide9": {
            "voice_id": "pqHfZKP75CvOlQylNhV4",
            "voice_name": "Bill",
            "text_with_tags": "[angry] ... текст с тегами эмоций ...",
            "text_plain": "... текст без тегов (fallback) ...",
            "output": "voice/voice_slide9.mp3"
        },
        "image_generations": [
            {
                "name": "slide1",
                "type": "image_to_image",
                "ref_images": ["shared/face_refs/olga/IMG_1142.jpg"],
                "prompt": "...",
                "output": "assets/slide1_real.png"
            },
            {
                "name": "slide5",
                "type": "image_to_image",
                "ref_images": ["shared/face_refs/olga/IMG_1142.jpg"],
                "prompt": "Selfie of the same girl, ...",
                "output": "assets/slide5_real.png"
            },
            {
                "name": "slide8",
                "type": "image_to_image",
                "ref_images": ["shared/face_refs/olga/IMG_1142.jpg"],
                "prompt": "...",
                "output": "assets/slide8_real.png"
            },
            {
                "name": "slide10",
                "type": "image_to_image",
                "ref_images": ["shared/face_refs/olga/IMG_1142.jpg"],
                "prompt": "Selfie of the same girl winking, ...",
                "output": "assets/slide10_real.png"
            }
        ]
    }
}


def main():
    if len(sys.argv) < 3:
        sys.exit("Usage: python scripts/new_reel.py <NN_name> <format>\n"
                 "Пример: python scripts/new_reel.py 02_lysaya whatsapp_prank")
    name = sys.argv[1]
    fmt = sys.argv[2]
    if fmt not in SKELETONS:
        sys.exit(f"ERROR: формат '{fmt}' не известен. Доступно: {list(SKELETONS)}")
    if not (TEMPLATES_DIR / f"{fmt}.json").exists():
        sys.exit(f"ERROR: template {fmt}.json не найден в templates/")

    target = REELS_DIR / name
    if target.exists():
        sys.exit(f"ERROR: {target} уже существует")

    for sub in ("refs", "assets", "mockups", "voice", "_build"):
        (target / sub).mkdir(parents=True)

    skeleton = SKELETONS[fmt]
    skeleton["name"] = name
    (target / "config.json").write_text(
        json.dumps(skeleton, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"✓ Создано: {target}")
    print(f"\nСледующие шаги:")
    print(f"  1. Отредактируй reels/{name}/config.json — впиши тексты переписки и промпты")
    print(f"  2. KIE_API_KEY=... python scripts/generate_images.py reels/{name}")
    print(f"  3. ELEVENLABS_API_KEY=... python scripts/generate_voice.py reels/{name}")
    print(f"  4. python scripts/build_mockups.py reels/{name}")
    print(f"  5. python scripts/add_titles.py reels/{name}")
    print(f"  6. python scripts/build_reel.py reels/{name}")


if __name__ == "__main__":
    main()
