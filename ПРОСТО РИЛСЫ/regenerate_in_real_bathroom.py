"""
Регенерация слайдов 1, 5, 8, 10 с использованием реальной ванной Olga (real_bathroom.jpg)
как второго референса. Слайд 8 — усиленный реализм для аргентинцев.
Слайды 1/5/10 — лицо Ольги (IMG_1142.jpg) + интерьер ванной.
Слайд 8 — только интерьер ванной + 5 реалистичных людей.
"""
import requests, time, os, json, threading

API_KEY = "9718cdee85415bb4096c0276bf5863bc"
CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
STATUS_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

FACE_REF = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/Креатив ап/Фото/Ольга/IMG_1142.jpg"
ROOM_REF = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ/real_bathroom.jpg"
OUT_DIR = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ"

IDENTITY_HEADER = """You are given TWO reference images:
- IMAGE 1 = the woman's face (CHARACTER REFERENCE — preserve identity exactly)
- IMAGE 2 = the actual bathroom interior of her apartment (LOCATION REFERENCE — preserve the exact layout, tiles, fixtures, lighting)

MANDATORY rules:
1. The woman's face must be IDENTICAL to IMAGE 1 — same bone structure, eyes, nose, lips, jaw, skin tone. Do NOT generate a new face.
2. The bathroom must match IMAGE 2 EXACTLY — same dark grey large-format matte tiles on walls and floor, same warm LED strip glow at the top of the wall, same large mirror over the bathtub, same glass shower screen, same suspended white toilet with grey lid, same white bidet, same white floating vanity. Do NOT invent a different bathroom — reproduce THIS one.
3. Apply ALL requested edits (pose, expression, props, steam, etc.) but keep face and bathroom identical to references.

Now apply the requested edit:

"""

REMINDER = "\n\nReminder: face from IMAGE 1, bathroom interior from IMAGE 2 — both must be preserved exactly. Apply all other edits fully."

# === Промпты ===

SLIDE_1_EDIT = """A vertical iPhone candid photo of the same woman from IMAGE 1, standing inside the exact bathroom from IMAGE 2 (dark grey tiles, warm LED glow, mirror over the bathtub, white toilet, bidet, vanity). She is wrapped in a white bath towel, holding a russian banya broom (a bundle of green oak and birch leaves on a wooden handle) resting on her shoulder. Long dark hair flowing down past her shoulders. Cheeks slightly flushed pink from heat. Thick white steam fills the room, fogging the mirror. She is looking directly at the camera with a playful slightly mischievous expression, head tilted slightly. The bathtub, glass shower screen, toilet and grey tiles must be visible behind her. Realistic candid amateur iPhone snapshot, slight motion blur, no studio lighting, raw skin texture."""

SLIDE_5_EDIT = """A vertical iPhone front-camera mirror selfie of the same woman from IMAGE 1, taken inside the exact bathroom from IMAGE 2 (dark grey tiles, warm LED glow, the large mirror over the bathtub). She is photographing herself in the bathroom mirror — face reflection clearly visible. Her face is heavily flushed red from heat and steam, sweat droplets visible on her temples and forehead, wet hair strands sticking to her forehead. Long dark hair partially down and damp. She is wrapped in a white bath towel, holding a russian banya broom (oak and birch leaves) raised to her shoulder, smartphone in the other hand for the selfie. The mirror is partially fogged with steam at the edges. Behind her in the reflection: dark grey tiles, glass shower screen, the white toilet visible. She is smiling proudly at the camera. Realistic iPhone front-camera selfie with slight lens distortion, vertical 9:16 framing, raw skin texture."""

SLIDE_10_EDIT = """A vertical iPhone front-camera mirror selfie of the same woman from IMAGE 1, inside the exact bathroom from IMAGE 2. She is winking at the camera with a confident smug smile. Russian banya broom (oak and birch leaves) resting casually on her shoulder. Wrapped in a white bath towel. Long dark hair flowing down past her shoulders on both sides. Cheeks slightly pink. Behind her in the mirror reflection: the dark grey tiled bathroom with warm LED light, glass shower screen, white toilet and bidet visible. Soft natural light. Realistic confident casual iPhone selfie, vertical 9:16."""

# === Slide 8 — реалистичные аргентинцы в её ванной (без лица Ольги) ===

SLIDE_8_PROMPT = """A vertical hyperrealistic iPhone candid photo, absurd surreal scene shot inside the exact bathroom from the reference image (IMAGE 1 = bathroom reference: dark grey large-format matte tiles, warm LED strip glow at top of wall, large mirror over bathtub with glass shower screen, suspended white toilet with grey lid, white bidet, white floating vanity with toiletries — match this bathroom EXACTLY).

Inside this small bathroom: FIVE real Latino Argentinian people crammed together — diverse, hyperrealistic, NOT model-pretty:
- A man around 50 with a beer belly, salt-and-pepper stubble, slightly bald
- A man around 30 with curly dark hair and glasses, lean
- A woman around 40 with curvy body, tan skin, dark wavy hair, no makeup
- A young man around 25, skinny, longer dark hair
- A woman around 28, tan skin, dark hair in messy bun

ALL of them wearing oversized authentic Russian fur ushanka hats (winter fur hats with ear flaps tied up) — this is critical and visually dominant.

Each person holding a russian banya broom (a bundle of green oak and birch leaves on a wooden handle).

All wrapped in white bath towels (men around waist, women around chest). Skin glistening with sweat, faces flushed red, expressions confused and overwhelmed but trying to enjoy. Some squinting from the heat.

Thick white steam everywhere, fogging the mirror, making the LED light glow softer. The bathroom is way too small for 5 people — one sitting on the closed white toilet lid, two squeezed together near the bidet, one leaning against the glass shower screen, one squeezed in the corner near the vanity.

Photographed as a candid iPhone snapshot from the bathroom doorway, slight wide-angle distortion, raw imperfect framing, ambient warm bathroom lighting plus iPhone flash bouncing off the steam, realistic skin pores and sweat, NO retouching, NO AI smoothness, NO plastic faces. Looks like a real party photo someone snapped on their phone. Vertical 9:16."""


def upload_ref(path, label):
    print(f"Загружаю {label}: {os.path.basename(path)}", flush=True)
    with open(path, "rb") as f:
        r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": (os.path.basename(path), f, "image/jpeg")}, timeout=60)
    url = r.json()["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")
    print(f"  URL: {url}", flush=True)
    return url


def create_task(prompt, refs):
    payload = {
        "model": "nano-banana-pro",
        "input": {"prompt": prompt, "aspect_ratio": "9:16", "resolution": "4K"},
    }
    if refs:
        payload["input"]["image_input"] = refs
    resp = requests.post(CREATE_URL, headers=HEADERS, json=payload, timeout=60)
    data = resp.json()
    if data.get("code") != 200:
        print(f"  ОШИБКА create: {data}", flush=True)
        return None
    return data["data"]["taskId"]


def poll_and_save(task_id, label, out_path):
    print(f"[{label}] taskId={task_id}, жду...", flush=True)
    for i in range(80):
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
    face_url = upload_ref(FACE_REF, "ЛИЦО")
    room_url = upload_ref(ROOM_REF, "ВАННАЯ")

    print("\nСоздаю 4 задачи параллельно...\n", flush=True)

    # Слайды с лицом + интерьер
    t1 = create_task(IDENTITY_HEADER + SLIDE_1_EDIT + REMINDER, [face_url, room_url])
    print(f"Слайд 1 task: {t1}", flush=True)
    t5 = create_task(IDENTITY_HEADER + SLIDE_5_EDIT + REMINDER, [face_url, room_url])
    print(f"Слайд 5 task: {t5}", flush=True)
    t10 = create_task(IDENTITY_HEADER + SLIDE_10_EDIT + REMINDER, [face_url, room_url])
    print(f"Слайд 10 task: {t10}", flush=True)
    # Слайд 8 — только интерьер
    t8 = create_task(SLIDE_8_PROMPT, [room_url])
    print(f"Слайд 8 task: {t8}", flush=True)

    threads = []
    for tid, label, fname in [
        (t1, "Слайд 1",  "slide1_real.png"),
        (t5, "Слайд 5",  "slide5_real.png"),
        (t10,"Слайд 10", "slide10_real.png"),
        (t8, "Слайд 8",  "slide8_real.png"),
    ]:
        if tid:
            t = threading.Thread(target=poll_and_save, args=(tid, label, os.path.join(OUT_DIR, fname)))
            t.start()
            threads.append(t)
    for t in threads:
        t.join()
    print("\nГотово.")


if __name__ == "__main__":
    main()
