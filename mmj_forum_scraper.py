"""
MMJ Forum Scraper — forum.mymorningjacket.net (SMF 2.1.6)
Publicly accessible, no login required.

Confirmed HTML structure:
  - Topic links: <a href="...?topic=N.0"> on board pages
  - Post body:   <div class="inner" data-msgid="N" id="msg_N">

Targets high-value boards:
  1 = The Band     (~60 pages)
  4 = The Music    (~40 pages)
  3 = The Tapings  (~30 pages)

Saves one .txt file per topic to 07-social/forum/<board_name>/
"""

import os
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

# Fix Windows console encoding for emoji/special chars in topic titles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(a) for a in args)
        print(text.encode("ascii", errors="replace").decode("ascii"), **kwargs)

BASE_URL = "https://forum.mymorningjacket.net/index.php"
OUTPUT_DIR = r"C:\MMJ-Corpus\07-social\forum"
DELAY = 1.2  # seconds between requests

HEADERS = {
    "User-Agent": "MMJCorpusBot/1.0 (educational RAG project; non-commercial)"
}

# board_id: (slug, max_pages)
BOARDS = {
    1: ("the_band",    60),
    4: ("the_music",   40),
    3: ("the_tapings", 30),
}


def fetch_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    time.sleep(DELAY)
    return BeautifulSoup(resp.text, "html.parser")


def get_topic_links(board_id, max_pages):
    """Yield (topic_id, title) from all pages of a board."""
    per_page = 20
    seen = set()

    for page_num in range(max_pages):
        start = page_num * per_page
        url = f"{BASE_URL}?board={board_id}.{start}"
        safe_print(f"  board {board_id} p{page_num+1}: {url}")
        try:
            soup = fetch_soup(url)
        except Exception as e:
            safe_print(f"    fetch error: {e}")
            break

        # Find anchor tags linking to topics with .0 (not #msg anchors)
        found = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = re.search(r"[?&]topic=(\d+)\.0(?:[^#]|$)", href)
            if not m:
                continue
            tid = int(m.group(1))
            if tid in seen:
                continue
            title = a.get_text(strip=True)
            # Skip date-like titles and short/empty titles
            if not title or len(title) < 4:
                continue
            if re.match(r"^\d{1,2}$", title):
                continue
            if re.search(r"\d{4},\s+\d{2}:\d{2}", title):
                continue
            seen.add(tid)
            found.append((tid, title))

        if not found:
            safe_print("    no new topics found — done")
            break

        yield from found


def get_topic_posts(topic_id):
    """Return list of post texts from all pages of a topic (max 8 pages)."""
    posts = []
    start = 0
    per_page = 15

    for _ in range(8):
        url = f"{BASE_URL}?topic={topic_id}.{start}"
        try:
            soup = fetch_soup(url)
        except Exception as e:
            safe_print(f"      fetch error: {e}")
            break

        # Post body: div.inner with data-msgid attribute
        page_posts = []
        for div in soup.find_all("div", class_="inner", attrs={"data-msgid": True}):
            text = div.get_text(separator=" ", strip=True)
            if text and len(text) > 15:
                page_posts.append(text)

        if not page_posts:
            break

        posts.extend(page_posts)

        # Find next page link
        next_start = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = re.search(rf"topic={topic_id}\.(\d+)", href)
            if m:
                s = int(m.group(1))
                if s > start:
                    if next_start is None or s < next_start:
                        next_start = s

        if next_start is None:
            break
        start = next_start

    return posts


def slugify(title, topic_id):
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "_", slug).strip("_")[:60]
    return f"{topic_id}_{slug}.txt"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    total_files = 0

    for board_id, (board_slug, max_pages) in BOARDS.items():
        safe_print(f"\n=== Board {board_id}: {board_slug} (up to {max_pages} pages) ===")
        board_dir = os.path.join(OUTPUT_DIR, board_slug)
        os.makedirs(board_dir, exist_ok=True)

        for topic_id, title in get_topic_links(board_id, max_pages):
            out_path = os.path.join(board_dir, slugify(title, topic_id))
            if os.path.exists(out_path):
                safe_print(f"    skip: [{topic_id}] {title[:50]}")
                continue

            safe_print(f"    [{topic_id}] {title[:60]}")
            posts = get_topic_posts(topic_id)
            if not posts:
                safe_print(f"      (empty)")
                continue

            content = (
                f"TOPIC: {title}\n"
                f"SOURCE: {BASE_URL}?topic={topic_id}.0\n"
                f"BOARD: {board_slug}\n\n"
                + "\n---\n".join(posts)
            )
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)

            total_files += 1
            safe_print(f"      {len(posts)} posts -> {os.path.basename(out_path)}")

    safe_print(f"\nDone. {total_files} topic files saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
