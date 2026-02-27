"""
MMJ RAGu Academy — Missing Albums Scraper (fixed)
"""

import requests
from bs4 import BeautifulSoup
import time
import os
import re

OUTPUT_DIR = r"C:\MMJ-Corpus\01-wikipedia"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

TARGETS = [
    ("at_dawn",    "https://en.wikipedia.org/w/index.php?action=raw&title=At_Dawn"),
    ("mmj_is",     "https://en.wikipedia.org/w/index.php?action=raw&title=Is_(My_Morning_Jacket_album)"),
]

def clean_wikitext(text):
    text = re.sub(r'\{\{[^}]*\}\}', '', text)
    text = re.sub(r'\[\[(?:File|Image):[^\]]*\]\]', '', text)
    text = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'={2,}(.+?)={2,}', r'\n\1\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def main():
    print("=" * 55)
    print("  MMJ RAGu Academy — Missing Albums Scraper")
    print("=" * 55)

    for name, url in TARGETS:
        print(f"\n  Fetching: {name}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            text = clean_wikitext(r.text)
            filepath = os.path.join(OUTPUT_DIR, f"{name}.txt")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            size = len(text)
            print(f"  ✓ {name}.txt — {size:,} chars")
            time.sleep(1)
        except Exception as e:
            print(f"  ✗ {name} — {e}")

    print(f"\n{'=' * 55}")
    print(f"  Done!")
    print(f"{'=' * 55}")

if __name__ == "__main__":
    main()
