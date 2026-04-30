import requests
import time
import os
import base64

API_KEY = "9718cdee85415bb4096c0276bf5863bc"
GENERATE_URL = "https://api.kie.ai/api/v1/gpt4o-image/generate"
STATUS_URL = "https://api.kie.ai/api/v1/gpt4o-image/record-info"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

FACE_REF = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/Ольга фото.JPG"
OUT = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ/test_neutral.png"

PROMPT = (
    "Use the face of the woman from the reference photo exactly. "
    "She is sitting in a cozy modern coffee shop in Buenos Aires, "
    "holding a cup of coffee, wearing a beige sweater, smiling. "
    "Natural window light, candid iPhone photo style."
)

with open(FACE_REF, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
img_uri = f"data:image/jpeg;base64,{b64}"

payload = {
    "prompt": PROMPT,
    "imageUrl": img_uri,
    "isEnhance": True,
    "enableFallback": True,
    "fallbackModel": "FLUX_MAX",
}

print("Создаю задачу...")
resp = requests.post(GENERATE_URL, headers=HEADERS, json=payload, timeout=60)
print(f"HTTP: {resp.status_code}")
print(f"Body: {resp.json()}")
data = resp.json()
task_id = data.get("data", {}).get("taskId")
if not task_id:
    print("Нет taskId")
    raise SystemExit

print(f"taskId: {task_id}")
print("Жду", end="", flush=True)
for _ in range(60):
    time.sleep(5)
    r = requests.get(STATUS_URL, headers=HEADERS, params={"taskId": task_id}, timeout=30)
    d = r.json().get("data", {}) or {}
    flag = d.get("successFlag")
    status = d.get("status", "")
    if flag == 1 or status == "SUCCESS":
        urls = d.get("response", {}).get("resultUrls", [])
        if urls:
            print(f"\nГотово: {urls[0]}")
            ir = requests.get(urls[0], timeout=60)
            with open(OUT, "wb") as f:
                f.write(ir.content)
            print(f"Сохранено: {OUT}")
            break
    if flag == 2 or status in ("FAILED", "failed", "ERROR"):
        print(f"\nОШИБКА: {d}")
        break
    print(".", end="", flush=True)
