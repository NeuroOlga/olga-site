"""
Генерация всех 4 слайдов рилса про баню (по правильному рецепту nano-banana-pro).
Слайды 1, 5, 10 — с лицом Ольги (image_input + identity header)
Слайд 8 — без лица (text-to-image, толпа аргентинцев)
"""
import requests
import time
import os
import json
import sys
import threading

API_KEY = "9718cdee85415bb4096c0276bf5863bc"
CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
STATUS_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

REF = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/Креатив ап/Фото/Ольга/IMG_1142.jpg"
OUT_DIR = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ"

IDENTITY_HEADER = """Use the supplied reference image as a CHARACTER REFERENCE for the person's face.

MANDATORY: Preserve the person's EXACT face from the reference — same bone structure, eyes, nose, lips, jaw, skin tone, and all distinguishing facial features. The person must be immediately recognizable as the same individual. Do NOT generate a new face. Reproduce existing tattoos in their original positions — do NOT invent new ones.

IMPORTANT: Apply ALL requested edits fully (clothing, pose, background, setting, lighting). Only the face identity must stay the same — everything else should change as described.

Now apply the requested edit:

"""

REMINDER = "\n\nReminder: preserve face from reference, but apply all other edits fully."

# === Промпты для каждого слайда ===

SLIDE_5_EDIT = """A vertical iPhone front-camera selfie of the same girl from the reference, taken inside a steamy modern bathroom. Her face is heavily flushed red from heat and steam, sweat droplets visible on her temples and forehead, wet hair strands sticking to her forehead. Long dark hair partially down. She is wrapped in a white bath towel, holding a russian banya broom (oak and birch leaves) raised to her shoulder in one hand, smartphone in the other hand for the selfie. Behind her: foggy bathroom mirror, white subway tiles, thick steam. She is smiling proudly at the camera. Realistic iPhone selfie with slight front-camera lens distortion, vertical 9:16 framing, raw skin texture. Keep all elements NOT mentioned unchanged."""

SLIDE_10_EDIT = """A vertical iPhone front-camera selfie of the same girl from the reference. She is winking at the camera with a confident smug smile. Russian banya broom (oak and birch leaves) resting casually on her shoulder. Wrapped in a white bath towel. Long dark hair flowing down past her shoulders on both sides. Cheeks slightly pink. Soft-focus background of a steamy modern bathroom with white subway tiles, Buenos Aires apartment vibe. Natural soft lighting. Realistic confident casual iPhone selfie, vertical 9:16. Keep all elements NOT mentioned unchanged."""

# === Слайд 8 — text-to-image без референса (толпа аргентинцев) ===

SLIDE_8_PROMPT = """A vertical iPhone amateur candid photo, absurd surreal scene. Five Latino Argentinian people (3 men, 2 women, ages 25-50, tan skin, dark hair) crammed inside a small modern apartment bathroom. ALL of them wearing oversized Russian fur ushanka hats (winter fur hats with ear flaps) — this is the most important visual element. Each person holding a russian banya broom (a bundle of green oak and birch leaves on a wooden handle). All wrapped in white bath towels. Faces flushed red, sweating heavily, looking confused and overwhelmed but trying to enjoy the experience. Thick white steam everywhere, foggy mirror, white subway tiles, modern gray fixtures. The bathroom is way too small for 5 people — one sitting on the toilet lid, others squeezed against walls and against the bathtub edge. Realistic chaotic phone snapshot, no staging, raw and a bit messy. Vertical 9:16 framing. Buenos Aires apartment bathroom."""


def upload_ref():
    print("Загружаю референс на tmpfiles...", flush=True)
    with open(REF, "rb") as f:
        r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": ("ref.jpg", f, "image/jpeg")}, timeout=60)
    url = r.json()["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")
    print(f"Референс: {url}", flush=True)
    return url


def create_task(prompt, ref_url=None):
    payload = {
        "model": "nano-banana-pro",
        "input": {
            "prompt": prompt,
            "aspect_ratio": "9:16",
            "resolution": "4K",
        },
    }
    if ref_url:
        payload["input"]["image_input"] = [ref_url]
    resp = requests.post(CREATE_URL, headers=HEADERS, json=payload, timeout=60)
    data = resp.json()
    if data.get("code") != 200:
        print(f"  ОШИБКА create: {data}", flush=True)
        return None
    return data["data"]["taskId"]


def poll_and_save(task_id, label, out_path):
    print(f"[{label}] taskId={task_id}, жду...", flush=True)
    for i in range(70):
        time.sleep(5)
        rr = requests.get(STATUS_URL, headers=HEADERS, params={"taskId": task_id}, timeout=30)
        d = rr.json().get("data", {}) or {}
        state = d.get("state", "")
        if state == "success":
            urls = json.loads(d.get("resultJson", "{}")).get("resultUrls", [])
            if urls:
                ir = requests.get(urls[0], timeout=120)
                with open(out_path, "wb") as f:
                    f.write(ir.content)
                print(f"[{label}] ✓ Сохранено: {out_path}", flush=True)
                return True
        if state in ("fail", "failed", "error"):
            print(f"[{label}] ✗ ОШИБКА: {d.get('failMsg')}", flush=True)
            return False
    print(f"[{label}] ✗ Таймаут", flush=True)
    return False


def main():
    ref_url = upload_ref()

    # Создаём все 3 задачи параллельно
    print("\nСоздаю 3 задачи параллельно...", flush=True)
    task5 = create_task(IDENTITY_HEADER + SLIDE_5_EDIT + REMINDER, ref_url)
    print(f"Слайд 5 task: {task5}", flush=True)
    task10 = create_task(IDENTITY_HEADER + SLIDE_10_EDIT + REMINDER, ref_url)
    print(f"Слайд 10 task: {task10}", flush=True)
    task8 = create_task(SLIDE_8_PROMPT, ref_url=None)
    print(f"Слайд 8 task: {task8}", flush=True)

    # Параллельный polling в потоках
    threads = []
    for tid, label, fname in [
        (task5, "Слайд 5", "slide5_selfie_red.png"),
        (task10, "Слайд 10", "slide10_final_wink.png"),
        (task8, "Слайд 8", "slide8_argentines.png"),
    ]:
        if tid:
            t = threading.Thread(target=poll_and_save, args=(tid, label, os.path.join(OUT_DIR, fname)))
            t.start()
            threads.append(t)

    for t in threads:
        t.join()

    print("\nГотово.", flush=True)


if __name__ == "__main__":
    main()
