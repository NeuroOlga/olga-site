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
OUT = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ/test_slide1_v4.png"

with open(REF, "rb") as f:
    r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": ("ref.jpg", f, "image/jpeg")}, timeout=60)
url = r.json()["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")
print(f"Референс: {url}", flush=True)

PROMPT = (
    "ЭТА ДЕВУШКА в ванной комнате с веником из дубовых и берёзовых листьев. "
    "Стоит в современной аргентинской квартире, в маленькой ванной с белой плиткой "
    "и серыми акцентами. Завёрнута в белое банное полотенце, держит веник на плече. "
    "Вокруг клубы густого белого пара. Щёки слегка раскраснелись от жара. "
    "Игривое, чуть лукавое выражение лица, смотрит прямо в камеру, голова немного наклонена.\n\n"
    "ВАЖНО: Лицо девушки должно быть ИДЕНТИЧНЫМ референсу — те же голубо-серые глаза, "
    "те же полные губы, тот же нос, тот же овал лица, те же густые брови, тот же цвет кожи. "
    "Это та же самая девушка с фотографии. "
    "Длинные прямые тёмные волосы спадают по обеим сторонам лица ниже плеч.\n\n"
    "Стиль: реальное любительское iPhone-фото, вертикальный кадр 9:16, естественное "
    "дневное освещение, реалистичная текстура кожи, без студийного света, как настоящий "
    "снимок с телефона."
)

payload = {
    "model": "nano-banana-pro",
    "input": {
        "prompt": PROMPT,
        "image_urls": [url],
        "output_format": "png",
        "image_size": "9:16",
    },
}

print("Создаю задачу...", flush=True)
resp = requests.post(CREATE_URL, headers=HEADERS, json=payload, timeout=60)
print(f"HTTP {resp.status_code}: {resp.json()}", flush=True)
task_id = resp.json().get("data", {}).get("taskId")
if not task_id:
    sys.exit(1)

print(f"taskId: {task_id}\nЖду", end="", flush=True)
for _ in range(120):
    time.sleep(5)
    rr = requests.get(STATUS_URL, headers=HEADERS, params={"taskId": task_id}, timeout=30)
    d = rr.json().get("data", {}) or {}
    state = d.get("state", "")
    if state == "success":
        urls = json.loads(d.get("resultJson", "{}")).get("resultUrls", [])
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
