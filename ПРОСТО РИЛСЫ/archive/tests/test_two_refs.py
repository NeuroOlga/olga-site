import requests
import time
import os
import json
import sys

API_KEY = "9718cdee85415bb4096c0276bf5863bc"
CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
STATUS_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

REF_FACE = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/Креатив ап/Фото/Ольга/IMG_1142.jpg"
REF_HAIR = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/Ольга фото.JPG"
OUT = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ/test_slide1_v3.png"


def upload(path):
    with open(path, "rb") as f:
        r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": (os.path.basename(path), f, "image/jpeg")}, timeout=60)
    url = r.json()["data"]["url"]
    return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")


print("Загружаю референсы...", flush=True)
url_face = upload(REF_FACE)
url_hair = upload(REF_HAIR)
print(f"Face: {url_face}", flush=True)
print(f"Hair: {url_hair}", flush=True)

PROMPT = (
    "Take the woman from the reference photos — her face must be EXACTLY identical "
    "to the reference selfie (IMG_1142): same blue-grey eyes, same full plump lips with "
    "strong cupid's bow, same thin sculpted nose, same defined high cheekbones, "
    "same thick dark eyebrows, same sharp jawline, same lightly tanned fair skin. "
    "Hair: very long, perfectly straight, dark brown almost black, falling down past "
    "her shoulders on BOTH sides of her face (as in the second reference photo). "
    "Do NOT change her face — this is the SAME PERSON.\n\n"
    "Scene: she is standing in a modern Buenos Aires apartment bathroom (white subway "
    "tiles, gray accents, minimalist), wrapped in a white bath towel. She holds a "
    "russian banya broom (large bundle of green oak and birch leaves on a wooden handle) "
    "resting on her shoulder. Thick white steam fills the room. Cheeks slightly flushed "
    "pink. Playful, slightly mischievous expression, looking directly at the camera, "
    "head tilted slightly.\n\n"
    "Style: candid amateur iPhone photo, vertical 9:16 frame, natural daylight, "
    "realistic skin texture with visible pores, no studio lighting, slight motion blur, "
    "looks like a real phone snapshot, NOT a stylized portrait."
)

payload = {
    "model": "nano-banana-pro",
    "input": {
        "prompt": PROMPT,
        "image_urls": [url_face, url_hair],
        "output_format": "png",
        "image_size": "9:16",
    },
}

print("\nСоздаю задачу...", flush=True)
resp = requests.post(CREATE_URL, headers=HEADERS, json=payload, timeout=60)
print(f"HTTP {resp.status_code}: {resp.json()}", flush=True)
data = resp.json()
task_id = data.get("data", {}).get("taskId")
if not task_id:
    print("Нет taskId", flush=True)
    sys.exit(1)

print(f"taskId: {task_id}\nЖду", end="", flush=True)
for i in range(120):
    time.sleep(5)
    r = requests.get(STATUS_URL, headers=HEADERS, params={"taskId": task_id}, timeout=30)
    d = r.json().get("data", {}) or {}
    state = d.get("state", "")
    if state == "success":
        rj = d.get("resultJson", "{}")
        urls = json.loads(rj).get("resultUrls", [])
        if urls:
            print(f"\nГотово: {urls[0]}", flush=True)
            ir = requests.get(urls[0], timeout=60)
            with open(OUT, "wb") as f:
                f.write(ir.content)
            print(f"Сохранено: {OUT}", flush=True)
            sys.exit(0)
    if state in ("fail", "failed", "error"):
        print(f"\nОШИБКА: {d}", flush=True)
        sys.exit(1)
    print(".", end="", flush=True)

print("\nТаймаут", flush=True)
