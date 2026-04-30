"""
Голосовое для слайда 9 через edge-tts (Microsoft, бесплатно).
Русский мужской голос Dmitry, с настройкой темпа/тона на крик.
"""
import asyncio
import edge_tts

OUT = "/Users/frolovaolga/Library/Mobile Documents/com~apple~CloudDocs/Olga Frolova/ПРОСТО РИЛСЫ/martin_voice_slide9.mp3"

# Текст с пунктуацией для интонаций (восклицания, паузы через ...)
TEXT = (
    "Олга, ты вообще нормальная?! "
    "Какая баня в моей квартире?! "
    "Я уже соседям снизу плачу за потоп!!! "
    "Убирайте всех немедленно... "
    "Я через двадцать минут буду, "
    "и если хоть один человек ещё там останется — "
    "я вызываю полицию! "
    "Ты слышишь меня?!"
)

async def main():
    # rate +10% (быстрее как от злости), pitch -10% (ниже = страшнее), volume +10
    communicate = edge_tts.Communicate(
        TEXT,
        voice="ru-RU-DmitryNeural",
        rate="+10%",
        pitch="-50Hz",
        volume="+10%",
    )
    await communicate.save(OUT)
    print(f"✓ Сохранено: {OUT}")

if __name__ == "__main__":
    asyncio.run(main())
