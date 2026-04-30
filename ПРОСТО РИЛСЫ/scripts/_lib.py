"""
Общая библиотека для скриптов сборки рилсов.

Каждый скрипт принимает путь к папке рилса (например `reels/01_banya`),
читает её `config.json`, мерджит с шаблоном из `templates/<format>.json`
и работает по получившемуся словарю.

Все пути в config.json — относительные. Они резолвятся либо относительно
папки рилса, либо относительно корня проекта (если начинаются с `shared/`).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
SHARED_DIR = PROJECT_ROOT / "shared"
REELS_DIR = PROJECT_ROOT / "reels"


def deep_merge(base: dict, override: dict) -> dict:
    """Рекурсивный мердж: override побеждает, dict-поля сливаются."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config(reel_dir: str | Path) -> dict:
    """Загрузить config.json рилса, смерджить с шаблоном по полю `format`."""
    reel_path = Path(reel_dir).resolve()
    config_path = reel_path / "config.json"
    if not config_path.exists():
        sys.exit(f"ERROR: config.json не найден: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    fmt = config.get("format")
    if fmt:
        template_path = TEMPLATES_DIR / f"{fmt}.json"
        if template_path.exists():
            with open(template_path, encoding="utf-8") as f:
                template = json.load(f)
            config = deep_merge(template, config)

    config["_reel_dir"] = str(reel_path)
    return config


def resolve_path(config: dict, p: str) -> Path:
    """
    Разрешить относительный путь из конфига в абсолютный.
    - `shared/...` или `templates/...` → от корня проекта
    - всё остальное → от папки рилса
    - абсолютный путь → как есть
    """
    if os.path.isabs(p):
        return Path(p)
    if p.startswith(("shared/", "templates/", "reels/", "archive/")):
        return PROJECT_ROOT / p
    return Path(config["_reel_dir"]) / p


def reel_path(config: dict, *parts: str) -> Path:
    """Сокращение для путей внутри папки рилса."""
    return Path(config["_reel_dir"]).joinpath(*parts)


def parse_reel_arg(argv: list[str]) -> Path:
    """Стандартный CLI: первый аргумент — путь к папке рилса."""
    if len(argv) < 2:
        script = os.path.basename(argv[0]) if argv else "script.py"
        sys.exit(f"Usage: python scripts/{script} <reel_dir>\nПример: python scripts/{script} reels/01_banya")
    p = Path(argv[1]).resolve()
    if not p.is_dir():
        sys.exit(f"ERROR: папка не найдена: {p}")
    return p
