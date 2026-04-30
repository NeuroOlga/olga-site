"""
Один шаг — собрать рилс целиком (после того, как фото и голос сгенерены).
Запускает: build_mockups → add_titles → build_reel.

Usage:
    python scripts/build_all.py reels/01_banya
"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script: str, reel_dir: str):
    print(f"\n{'='*60}\n {script}\n{'='*60}")
    res = subprocess.run([sys.executable, os.path.join(HERE, script), reel_dir])
    if res.returncode != 0:
        sys.exit(f"\n!! {script} failed (code {res.returncode})")


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python scripts/build_all.py <reel_dir>")
    reel_dir = sys.argv[1]
    run("build_mockups.py", reel_dir)
    run("add_titles.py", reel_dir)
    run("build_reel.py", reel_dir)
    print("\n🎬 Полностью собрано.")


if __name__ == "__main__":
    main()
