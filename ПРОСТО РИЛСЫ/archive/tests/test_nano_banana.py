import requests
import time
import os
import json

API_KEY = "9718cdee85415bb4096c0276bf5863bc"
CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
STATUS_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

FACE_REF = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/Ольга фото.JPG"
OUT = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ/test_slide1_banya.png"

# Шаг 1: загрузка фото на tmpfiles.org
print("Загружаю референс на tmpfiles.org...")
with open(FACE_REF, "rb") as f:
    up = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": ("face.jpg", f, "image/jpeg")}, timeout=60)
up_data = up.json()
print(f"Ответ tmpfiles: {up_data}")
view_url = up_data["data"]["url"]
direct_url = view_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
print(f"Public URL: {direct_url}")

# Шаг 2: создание задачи nano-banana-pro
PROMPT = (
    "Take the EXACT girl from the reference photo. Keep her face 100% identical to the reference: "
    "same face shape, same eyes, same nose, same lips, same eyebrows, same skin tone. "
    "Do NOT change her facial features in any way. This is a photo of THE SAME PERSON.\n\n"
    "Place this exact girl into a new scene: she is standing in a modern Buenos Aires "
    "apartment bathroom (white tiles, gray accents, minimalist), wrapped in a white bath towel, "
    "holding a russian banya broom (bundle of green oak and birch leaves on a wooden handle) "
    "over her shoulder. Long dark brunette hair flowing down (as in reference). "
    "Thick white steam fills the room. Cheeks slightly flushed pink from the heat. "
    "Playful, slightly mischievous expression, looking at the camera.\n\n"
    "Style: candid iPhone photo, vertical 9:16, natural daylight, realistic skin texture, "
    "no studio lighting, slight imperfection like a real phone snapshot."
)

payload = {
    "model": "nano-banana-pro",
    "input": {
        "prompt": PROMPT,
        "image_urls": [direct_url],
        "output_format": "png",
        "image_size": "9:16",
    },
}

print("\nСоздаю задачу nano-banana-pro...")
resp = requests.post(CREATE_URL, headers=HEADERS, json=payload, timeout=60)
print(f"HTTP {resp.status_code}: {resp.json()}")
data = resp.json()
task_id = data.get("data", {}).get("taskId") or data.get("data", {}).get("id")
if not task_id:
    print("Нет taskId")
    raise SystemExit

print(f"taskId: {task_id}")
print("Жду", end="", flush=True)
for _ in range(60):
    time.sleep(5)
    r = requests.get(STATUS_URL, headers=HEADERS, params={"taskId": task_id}, timeout=30)
    d = r.json().get("data", {}) or {}
    state = d.get("state", "")
    if state == "success":
        rj = d.get("resultJson", "{}")
        try:
            urls = json.loads(rj).get("resultUrls", [])
        except Exception:
            urls = []
        if urls:
            print(f"\nГотово: {urls[0]}")
            ir = requests.get(urls[0], timeout=60)
            with open(OUT, "wb") as f:
                f.write(ir.content)
            print(f"Сохранено: {OUT}")
            break
        else:
            print(f"\nНет URL в resultJson: {rj}")
            break
    if state in ("fail", "failed", "error"):
        print(f"\nОШИБКА: {d}")
        break
    print(".", end="", flush=True)
else:
    print("\nТаймаут")
