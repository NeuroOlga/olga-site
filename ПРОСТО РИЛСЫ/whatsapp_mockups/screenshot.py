"""Снимает все HTML-мокапы WhatsApp в PNG 1080x1920."""
import sys, os, glob
from playwright.sync_api import sync_playwright

DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    files = sorted(glob.glob(os.path.join(DIR, "slide*.html")))
    if not files:
        print("Нет HTML файлов")
        return
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)
        page = ctx.new_page()
        for f in files:
            out = f.replace(".html", ".png")
            page.goto("file://" + f)
            page.wait_for_load_state("networkidle")
            page.screenshot(path=out, full_page=False, omit_background=False)
            print(f"✓ {os.path.basename(out)}")
        browser.close()

if __name__ == "__main__":
    main()
