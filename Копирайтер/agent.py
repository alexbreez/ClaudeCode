#!/usr/bin/env python3
"""
Telegram Copywriter Agent
Интерактивный CLI-агент для генерации постов в твоём стиле.
"""

import os
import sys
import glob
from pathlib import Path
from dotenv import load_dotenv
import anthropic

load_dotenv()

BASE_DIR = Path(__file__).parent
DIRS = {
    "my_posts":    BASE_DIR / "01_мой_канал",
    "competitors": BASE_DIR / "02_конкуренты",
    "style":       BASE_DIR / "03_стиль",
    "audience":    BASE_DIR / "04_аудитория",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def read_dir(path: Path) -> str:
    """Читает все .md файлы из папки и возвращает их содержимое."""
    files = sorted(path.glob("*.md"))
    if not files:
        return "(файлы не найдены)"
    parts = []
    for f in files:
        parts.append(f"### {f.name}\n{f.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def build_context() -> str:
    """Формирует системный контекст из всех папок."""
    my_posts    = read_dir(DIRS["my_posts"])
    competitors = read_dir(DIRS["competitors"])
    style       = read_dir(DIRS["style"])
    audience    = read_dir(DIRS["audience"])

    return f"""Ты — профессиональный копирайтер для Telegram-канала.
Твоя задача — писать посты точно в голосе автора, для его аудитории.

## МОЙ СТИЛЬ (brand voice)
{style}

## МОЯ АУДИТОРИЯ
{audience}

## МОИ ПОСТЫ (референс голоса)
{my_posts}

## ПОСТЫ КОНКУРЕНТОВ (для вдохновения по форматам и темам)
{competitors}

---
ПРАВИЛА:
- Пиши ТОЛЬКО в стиле автора из раздела «МОЙ СТИЛЬ».
- Не используй запрещённые фразы и обороты.
- Адаптируй удачные форматы конкурентов — но не копируй текст.
- Каждый пост должен быть полезен для аудитории из раздела «МОЯ АУДИТОРИЯ».
- Не добавляй лишних пояснений — выдавай только готовый пост.
"""


def ask_claude(system: str, user_message: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "[ОШИБКА] ANTHROPIC_API_KEY не найден. Добавь его в файл .env"

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


# ── команды агента ────────────────────────────────────────────────────────────

def cmd_post(topic: str) -> None:
    """Генерирует пост на заданную тему."""
    print("\n⏳ Генерирую пост...\n")
    context = build_context()
    prompt = f"Напиши Telegram-пост на тему: «{topic}»"
    result = ask_claude(context, prompt)
    print("─" * 60)
    print(result)
    print("─" * 60)


def cmd_analyze_style() -> None:
    """Анализирует посты автора и составляет brand voice."""
    my_posts = read_dir(DIRS["my_posts"])
    if "(файлы не найдены)" in my_posts:
        print("\n[!] Добавь посты в папку 01_мой_канал/ и попробуй снова.")
        return

    print("\n⏳ Анализирую твой стиль...\n")
    system = (
        "Ты — аналитик стиля письма. "
        "Твоя задача — изучить тексты и описать уникальный голос автора."
    )
    prompt = f"""Проанализируй эти посты и составь подробное описание brand voice автора:

{my_posts}

Структура ответа:
1. Тон и интонация
2. Характерные обороты и слова (минимум 10)
3. Запрещённые слова / чего автор избегает
4. Структура типичного поста
5. Таблица DO / DON'T (15 примеров)

Сохрани результат — это основа для файла 03_стиль/brand_voice.md"""

    result = ask_claude(system, prompt)
    print("─" * 60)
    print(result)
    print("─" * 60)
    save = input("\nСохранить результат в 03_стиль/brand_voice.md? [y/N]: ").strip().lower()
    if save == "y":
        path = DIRS["style"] / "brand_voice.md"
        path.write_text(result, encoding="utf-8")
        print(f"[✓] Сохранено в {path}")


def cmd_analyze_competitors() -> None:
    """Анализирует посты конкурентов и выделяет лучшие форматы."""
    competitors = read_dir(DIRS["competitors"])
    if "(файлы не найдены)" in competitors:
        print("\n[!] Добавь посты конкурентов в папку 02_конкуренты/ и попробуй снова.")
        return

    print("\n⏳ Анализирую конкурентов...\n")
    system = "Ты — стратег контента. Анализируешь конкурентов и выявляешь выигрышные паттерны."
    prompt = f"""Проанализируй посты конкурентов и выдай:

{competitors}

1. ТОП-5 форматов/структур, которые работают
2. Темы, которые вызывают наибольший отклик
3. Крючки (первые строки), которые цепляют
4. Что стоит адаптировать под мой канал (без копирования)
5. Что конкуренты делают плохо — где можно выиграть"""

    result = ask_claude(system, prompt)
    print("─" * 60)
    print(result)
    print("─" * 60)


def cmd_content_plan(period: str = "неделю") -> None:
    """Генерирует контент-план на неделю или месяц."""
    print(f"\n⏳ Генерирую контент-план на {period}...\n")
    context = build_context()
    prompt = f"""Составь контент-план на {period} для моего Telegram-канала.

Формат каждого пункта:
- День/дата
- Тема поста
- Формат (история / список / кейс / мнение / лайфхак / и т.д.)
- Одна строка — о чём пост (хук)

Учитывай мой стиль, аудиторию и лучшие форматы конкурентов."""

    result = ask_claude(context, prompt)
    print("─" * 60)
    print(result)
    print("─" * 60)


def cmd_critique() -> None:
    """Критикует готовый пост: стиль, хук, CTA."""
    print("\nВставь пост для критики (введи END на новой строке для завершения):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)

    post_text = "\n".join(lines).strip()
    if not post_text:
        print("[!] Пост пустой.")
        return

    print("\n⏳ Анализирую пост...\n")
    context = build_context()
    prompt = f"""Проверь этот пост по 5 критериям:

{post_text}

1. СТИЛЬ — соответствует ли моему голосу? Что нарушает?
2. ХУК — цепляет ли первая строка? Дай улучшенный вариант.
3. СТРУКТУРА — логика, читаемость, абзацы.
4. ПОЛЬЗА для аудитории — есть ли конкретная ценность?
5. CTA — есть ли призыв к действию? Какой поставить?

В конце: итоговая оценка /10 и переписанный улучшенный вариант поста."""

    result = ask_claude(context, prompt)
    print("─" * 60)
    print(result)
    print("─" * 60)


def cmd_help() -> None:
    print("""
╔══════════════════════════════════════════════════════╗
║         TELEGRAM COPYWRITER AGENT  —  команды       ║
╠══════════════════════════════════════════════════════╣
║  пост <тема>      Сгенерировать пост на тему         ║
║  стиль            Проанализировать мой стиль письма  ║
║  конкуренты       Разобрать посты конкурентов        ║
║  план             Контент-план на неделю             ║
║  план месяц       Контент-план на месяц              ║
║  критика          Разбор и улучшение поста           ║
║  помощь           Показать эту справку               ║
║  выход            Завершить работу                   ║
╚══════════════════════════════════════════════════════╝
""")


# ── main loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n🤖 Telegram Copywriter Agent запущен.")
    print("   Введи 'помощь' чтобы увидеть доступные команды.\n")

    while True:
        try:
            raw = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nПока!")
            sys.exit(0)

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("выход", "exit", "quit"):
            print("Пока!")
            break
        elif cmd in ("помощь", "help"):
            cmd_help()
        elif cmd == "пост":
            if not arg:
                print("[!] Укажи тему: пост <тема>")
            else:
                cmd_post(arg)
        elif cmd == "стиль":
            cmd_analyze_style()
        elif cmd == "конкуренты":
            cmd_analyze_competitors()
        elif cmd == "план":
            period = arg if arg else "неделю"
            cmd_content_plan(period)
        elif cmd == "критика":
            cmd_critique()
        else:
            print(f"[?] Неизвестная команда: '{cmd}'. Введи 'помощь' для списка команд.")


if __name__ == "__main__":
    main()
