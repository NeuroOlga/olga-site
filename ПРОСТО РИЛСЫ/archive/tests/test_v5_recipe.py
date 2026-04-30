"""
Генерация по официальному рецепту Nano Banana Pro:
- image_input (НЕ image_urls)
- aspect_ratio + resolution (НЕ image_size)
- Identity header добавляется программно
- Прямой английский промпт
- 4K resolution
"""
import requests
import time
import os
import json
import sys

API_KEY = "9718cdee85415bb4096c0276bf5863bc"
CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
STATUS_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

REF = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/Креатив ап/Фото/Ольга/IMG_1142.jpg"
OUT = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ/test_slide1_v5.png"

# Identity header — точная формулировка из рецепта
IDENTITY_HEADER = """Use the supplied reference image as a CHARACTER REFERENCE for the person's face.

MANDATORY: Preserve the person's EXACT face from the reference — same bone structure, eyes, nose, lips, jaw, skin tone, and all distinguishing facial features. The person must be immediately recognizable as the same individual. Do NOT generate a new face. Reproduce existing tattoos in their original positions — do NOT invent new ones.

IMPORTANT: Apply ALL requested edits fully (clothing, pose, background, setting, lighting). Only the face identity must stay the same — everything else should change as described.

Now apply the requested edit:

"""

EDIT_INSTRUCTION = """A close-up vertical iPhone photo of the same girl from the reference, standing in a modern Buenos Aires apartment bathroom with white subway tiles and gray accents. She is wrapped in a white bath towel, holding a russian banya broom (a bundle of green oak and birch leaves on a wooden handle) resting on her shoulder. Long dark hair flowing down past her shoulders on both sides of her face. Cheeks slightly flushed pink from the heat. Thick white steam fills the room. Her expression is playful and slightly mischievous, looking directly at the camera with head tilted slightly. Natural daylight from a small window. Realistic candid amateur phone snapshot, slight motion blur, no studio lighting, raw skin texture. Keep all elements NOT mentioned in this request unchanged."""

REMINDER = "\n\nReminder: preserve face from reference, but apply all other edits fully."

PROMPT = IDENTITY_HEADER + EDIT_INSTRUCTION + REMINDER

# Загружаем фото
print("Загружаю референс...", flush=True)
with open(REF, "rb") as f:
    r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": ("ref.jpg", f, "image/jpeg")}, timeout=60)
url = r.json()["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")
print(f"Референс URL: {url}", flush=True)

# Правильный payload
payload = {
    "model": "nano-banana-pro",
    "input": {
        "prompt": PROMPT,
        "image_input": [url],          # <-- правильное поле
        "aspect_ratio": "9:16",        # <-- правильный параметр
        "resolution": "4K",            # <-- 4K качество
    },
}

print("Создаю задачу с правильным форматом...", flush=True)
resp = requests.post(CREATE_URL, headers=HEADERS, json=payload, timeout=60)
print(f"HTTP {resp.status_code}: {resp.json()}", flush=True)
data = resp.json()
if data.get("code") != 200:
    print("ОШИБКА создания", flush=True)
    sys.exit(1)
task_id = data["data"]["taskId"]
print(f"taskId: {task_id}\nЖду (4K = до 5 минут)", end="", flush=True)

for _ in range(70):
    time.sleep(5)
    rr = requests.get(STATUS_URL, headers=HEADERS, params={"taskId": task_id}, timeout=30)
    d = rr.json().get("data", {}) or {}
    state = d.get("state", "")
    if state == "success":
        urls = json.loads(d.get("resultJson", "{}")).get("resultUrls", [])
        if urls:
            print(f"\nГотово: {urls[0]}", flush=True)
            ir = requests.get(urls[0], timeout=120)
            with open(OUT, "wb") as f:
                f.write(ir.content)
            print(f"Сохранено: {OUT}", flush=True)
            sys.exit(0)
    if state in ("fail", "failed", "error"):
        print(f"\nОШИБКА: failMsg={d.get('failMsg')}, failCode={d.get('failCode')}", flush=True)
        sys.exit(1)
    print(".", end="", flush=True)
print("\nТаймаут", flush=True)
