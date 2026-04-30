import requests
import time
import os
import base64
import mimetypes

API_KEY = "9718cdee85415bb4096c0276bf5863bc"
GENERATE_URL = "https://api.kie.ai/api/v1/gpt4o-image/generate"
STATUS_URL = "https://api.kie.ai/api/v1/gpt4o-image/record-info"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FACE_REF = os.path.join(os.path.dirname(SCRIPT_DIR), "Ольга фото.JPG")
OUT_PATH = os.path.join(SCRIPT_DIR, "test_slide1_banya.png")

PROMPT = (
    "iPhone candid amateur photo, vertical portrait. "
    "The same young woman from the reference photo (long dark brunette hair, "
    "blue eyes, full lips, fair skin, slim build) — keep her face EXACTLY like in the reference. "
    "She is wrapped in a white bath towel, holding a Russian banya broom "
    "(a bundle of green oak and birch leaves on a wooden handle) over her shoulder. "
    "Standing in a modern Buenos Aires apartment bathroom with white tiles "
    "and gray accents, minimalist design. Thick white steam billowing around her. "
    "Her cheeks are slightly flushed pink from the heat. Playful, mischievous expression, "
    "looking at the camera. Natural daylight. Looks like a real iPhone snapshot, "
    "no studio lighting, slight imperfection, realistic skin texture."
)

def to_data_uri(path):
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/jpeg"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"

def main():
    print(f"Использую референс: {FACE_REF}")
    if not os.path.exists(FACE_REF):
        print(f"ОШИБКА: не найден файл с лицом")
        return

    print("Кодирую фото в base64...")
    img_uri = to_data_uri(FACE_REF)

    payload = {
        "prompt": PROMPT,
        "imageUrl": img_uri,
        "isEnhance": True,
        "enableFallback": True,
        "fallbackModel": "FLUX_MAX",
    }

    print("Создаю задачу в KIE.ai...")
    resp = requests.post(GENERATE_URL, headers=HEADERS, json=payload, timeout=60)
    data = resp.json()
    print(f"Ответ: {data}")
    if resp.status_code != 200 or data.get("code") not in (200, 0):
        print(f"ОШИБКА: {data}")
        return

    task_id = data.get("data", {}).get("taskId") or data.get("data", {}).get("task_id")
    if not task_id:
        print(f"Нет taskId в ответе")
        return

    print(f"taskId: {task_id}")
    print("Жду результат", end="", flush=True)

    for i in range(60):
        time.sleep(5)
        r = requests.get(STATUS_URL, headers=HEADERS, params={"taskId": task_id}, timeout=30)
        d = r.json().get("data", {}) or {}
        flag = d.get("successFlag")
        status = d.get("status", "")
        if flag == 1 or status == "SUCCESS":
            urls = d.get("response", {}).get("resultUrls", [])
            if urls:
                print(f"\nГотово: {urls[0]}")
                img_resp = requests.get(urls[0], timeout=60)
                with open(OUT_PATH, "wb") as f:
                    f.write(img_resp.content)
                print(f"Сохранено: {OUT_PATH}")
                return
        if flag == 2 or status in ("FAILED", "failed", "ERROR"):
            print(f"\nОШИБКА генерации: {d.get('errorMessage')}")
            return
        print(".", end="", flush=True)

    print("\nТаймаут")

if __name__ == "__main__":
    main()
