# ПРОСТО РИЛСЫ

Фабрика Instagram-рилсов в формате WhatsApp-пранка (и других). Каждый рилс
живёт в своей папке `reels/<NN_name>/` и описан одним `config.json`.
Скрипты в `scripts/` универсальные — работают с любым рилсом по его конфигу.

---

## Структура

```
ПРОСТО РИЛСЫ/
├── reels/                          # ← каждое видео = одна папка
│   └── 01_banya/
│       ├── config.json             # сценарий, тексты, голос, длительности
│       ├── refs/                   # входные референсы (фото квартиры и т.д.)
│       ├── assets/                 # AI-сгенерённые финальные кадры (slide1/5/8/10)
│       ├── mockups/                # WhatsApp PNG-мокапы (slide2..8 + s9 mp4)
│       ├── voice/                  # TTS голосовое (slide 9)
│       ├── _build/                 # промежуточные HTML/tmp (gitignore)
│       └── final.mp4               # ← готовый рилс
│
├── shared/                         # общее на все рилсы
│   ├── face_refs/{olga,anatoliy,timur}/  # фото для AI-генерации
│   ├── music/background_music.mp3
│   └── voices/                     # библиотека voice_id ElevenLabs (опционально)
│
├── scripts/                        # универсальные, читают config.json рилса
│   ├── _lib.py                     # загрузка конфига, мердж шаблона
│   ├── new_reel.py                 # скаффолдинг нового рилса из шаблона
│   ├── generate_images.py          # KIE.ai → assets/
│   ├── generate_voice.py           # ElevenLabs → voice/
│   ├── build_mockups.py            # WhatsApp PNG → mockups/
│   ├── add_titles.py               # хук+финал надписи на slide1/10
│   ├── build_reel.py               # финальная сборка → final.mp4
│   └── build_all.py                # mockups → titles → reel одной командой
│
├── templates/                      # JSON-шаблоны форматов
│   └── whatsapp_prank.json         # дефолты для всех whatsapp-пранков
│
└── archive/                        # старые тесты и эксперименты
```

---

## Workflow: новый рилс с нуля

```bash
# 1. Скаффолдинг
python scripts/new_reel.py 02_lysaya whatsapp_prank
# → создаст reels/02_lysaya/{refs,assets,mockups,voice,_build}/ + config.json

# 2. Отредактируй reels/02_lysaya/config.json
#    - chat.recipient_name / recipient_avatar_letter
#    - thread (тексты переписки s2..s8)
#    - photos (ключи, на которые ссылается thread)
#    - title_slide_1.lines + title_slide_10 (финал)
#    - voice_slide9.text_with_tags + voice_id
#    - image_generations[].prompt

# 3. Сгенерируй фото (5–10 минут)
KIE_API_KEY=... python scripts/generate_images.py reels/02_lysaya
# → reels/02_lysaya/assets/slide{1,5,8,10}_real.png
# Можно частично: --only slide5,slide8

# 4. Сгенерируй голосовое
ELEVENLABS_API_KEY=... python scripts/generate_voice.py reels/02_lysaya
# → reels/02_lysaya/voice/voice_slide9.mp3

# 5. Сборка (всё одной командой)
python scripts/build_all.py reels/02_lysaya
# → reels/02_lysaya/final.mp4
```

Если правишь только текст переписки — достаточно `build_mockups.py` + `build_reel.py`.
Если правишь только хук-надпись — `add_titles.py` + `build_reel.py`.

---

## Конвенции

- **Имя папки рилса:** `NN_короткое_имя` (порядковый номер для сортировки).
- **Финальный файл:** всегда `final.mp4` внутри папки рилса. Перед публикацией
  переименуй вручную (`final.mp4` → `lysaya.mp4`) и заливай в Instagram.
- **Все пути в config.json:**
  - `assets/...`, `refs/...`, `voice/...`, `mockups/...` — от папки рилса
  - `shared/...`, `templates/...` — от корня проекта
- **Что под git:**
  - `reels/<name>/config.json`, `assets/`, `mockups/*.png`, `voice/*.mp3`, `final.mp4` — да
  - `_build/` — нет (промежуточные HTML/tmp)
- **Шаблоны:** `templates/<format>.json` хранит дефолты (длительности слайдов,
  музыка, ducking, размеры шрифтов, safe-zone). `config.json` рилса
  переопределяет нужные поля. Загрузка через `_lib.load_config()`.

---

## Формат whatsapp_prank (10 слайдов, ~38 сек)

См. `templates/whatsapp_prank.json` и `reels/01_banya/config.json` как эталон.

| # | Что                              | Откуда           |
|---|----------------------------------|------------------|
| 1 | Хук-фото с белой надписью        | `assets/slide1_with_title.png` (генерация + add_titles) |
| 2 | Ольга пишет получателю + фото    | `mockups/slide2_*.png` |
| 3 | Реакция «😳😳😳»                  | `mockups/slide3_*.png` |
| 4 | Возмущение получателя            | `mockups/slide4_*.png` |
| 5 | Селфи Ольги (полноэкранно)       | `assets/slide5_real.png` |
| 6 | Угроза получателя                | `mockups/slide6_*.png` |
| 7 | Приказ получателя                | `mockups/slide7_*.png` |
| 8 | Эскалация — Ольга + фото         | `mockups/slide8_*.png` |
| 9 | Голосовое (соло, анимация 22 с)  | `mockups/slide9_voice.mp4` + `voice/voice_slide9.mp3` |
| 10| Финал-якорь с надписью           | `assets/slide10_with_title.png` |

Instagram safe-zone: WhatsApp-мокап вписан в центр кадра 1080×1920,
вокруг чёрные поля (~360px сверху, ~600px снизу, ~97px по бокам), содержимое
чата масштабировано до 82% — чтобы ник IG / подпись / лайки не перекрывали.

---

## API-ключи

В environment (не коммитить):
- `KIE_API_KEY` — для `generate_images.py` (KIE.ai nano-banana-pro)
- `ELEVENLABS_API_KEY` — для `generate_voice.py`

Можно положить в `~/.zshrc`:
```bash
export KIE_API_KEY=9718cdee85415bb4096c0276bf5863bc
export ELEVENLABS_API_KEY=sk_...
```

---

## Зависимости

Python 3.10+:
- `playwright` (для рендера WhatsApp HTML → PNG)
- `Pillow` (надписи)
- `requests` (KIE.ai, ElevenLabs)

ffmpeg — `~/bin/ffmpeg` (см. `FFMPEG` в скриптах).

```bash
pip install playwright Pillow requests
playwright install chromium
```
