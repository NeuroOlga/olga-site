"""
Генерация AI-изображений для рилса через KIE.ai (nano-banana-pro).

Берёт image_generations[] из config.json. Для каждой записи:
- type=text_to_image: чистый промпт без референса
- type=image_to_image: грузит ref_images на tmpfiles, передаёт как image_input

API-ключ — из ENV `KIE_API_KEY`.

Usage:
    KIE_API_KEY=... python scripts/generate_images.py reels/01_banya
    KIE_API_KEY=... python scripts/generate_images.py reels/01_banya --only slide5,slide8
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import load_config, parse_reel_arg, resolve_path


CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
STATUS_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"


IDENTITY_HEADER = """Use the supplied reference image(s) as a CHARACTER REFERENCE for the person's face.

MANDATORY: Preserve the person's EXACT face from the reference — same bone structure, eyes, nose, lips, jaw, skin tone, and all distinguishing facial features. The person must be immediately recognizable as the same individual. Do NOT generate a new face. Reproduce existing tattoos in their original positions — do NOT invent new ones.

IMPORTANT: Apply ALL requested edits fully (clothing, pose, background, setting, lighting). Only the face identity must stay the same — everything else should change as described.

Now apply the requested edit:

"""

REMINDER = "\n\nReminder: preserve face from reference, but apply all other edits fully."


def upload_ref(path: str) -> str:
    with open(path, "rb") as f:
        r = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": (os.path.basename(path), f, "image/jpeg")},
            timeout=60,
        )
    return r.json()["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")


def create_task(api_key: str, prompt: str, ref_urls: list[str] | None = None) -> str | None:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "nano-banana-pro",
        "input": {
            "prompt": prompt,
            "aspect_ratio": "9:16",
            "resolution": "4K",
        },
    }
    if ref_urls:
        payload["input"]["image_input"] = ref_urls
    r = requests.post(CREATE_URL, headers=headers, json=payload, timeout=60)
    data = r.json()
    if data.get("code") != 200:
        print(f"  ! create error: {data}")
        return None
    return data["data"]["taskId"]


def poll_and_save(api_key: str, task_id: str, label: str, out_path: Path) -> bool:
    headers = {"Authorization": f"Bearer {api_key}"}
    print(f"  [{label}] taskId={task_id}, жду...")
    for _ in range(70):
        time.sleep(5)
        rr = requests.get(STATUS_URL, headers=headers, params={"taskId": task_id}, timeout=30)
        d = rr.json().get("data", {}) or {}
        state = d.get("state", "")
        if state == "success":
            urls = json.loads(d.get("resultJson", "{}")).get("resultUrls", [])
            if urls:
                ir = requests.get(urls[0], timeout=120)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(ir.content)
                print(f"  [{label}] ✓ {out_path.name}")
                return True
        if state in ("fail", "failed", "error"):
            print(f"  [{label}] ✗ {d.get('failMsg')}")
            return False
    print(f"  [{label}] ✗ timeout")
    return False


def main():
    reel_dir = parse_reel_arg(sys.argv)
    config = load_config(reel_dir)
    api_key = os.environ.get("KIE_API_KEY")
    if not api_key:
        sys.exit("ERROR: задай KIE_API_KEY в env")

    only = None
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        only = set(sys.argv[idx + 1].split(","))

    gens = config.get("image_generations", [])
    if not gens:
        sys.exit("ERROR: image_generations не задан в config")

    if only:
        gens = [g for g in gens if g["name"] in only]
        print(f"Фильтр --only: {len(gens)} задач")

    # Загружаем референсы (уникальные пути)
    ref_paths = set()
    for g in gens:
        for r in g.get("ref_images", []):
            ref_paths.add(str(resolve_path(config, r)))
    ref_url_cache = {}
    if ref_paths:
        print(f"Загружаю {len(ref_paths)} референсов на tmpfiles...")
        for rp in ref_paths:
            url = upload_ref(rp)
            ref_url_cache[rp] = url
            print(f"  {os.path.basename(rp)} → {url}")

    # Создаём все задачи параллельно
    print(f"\nСоздаю {len(gens)} задач параллельно...")
    tasks = []
    for g in gens:
        if g["type"] == "image_to_image":
            ref_urls = [ref_url_cache[str(resolve_path(config, r))] for r in g["ref_images"]]
            prompt = IDENTITY_HEADER + g["prompt"] + REMINDER
        else:
            ref_urls = None
            prompt = g["prompt"]
        tid = create_task(api_key, prompt, ref_urls)
        out = resolve_path(config, g["output"])
        tasks.append((tid, g["name"], out))
        print(f"  {g['name']}: task={tid}")

    # Параллельный polling
    threads = []
    for tid, label, out in tasks:
        if tid:
            t = threading.Thread(target=poll_and_save, args=(api_key, tid, label, out))
            t.start()
            threads.append(t)
    for t in threads:
        t.join()

    print("\nГотово.")


if __name__ == "__main__":
    main()
