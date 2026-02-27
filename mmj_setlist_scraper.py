"""
MMJ RAGu Academy — Setlist Scraper
Scrapes My Morning Jacket setlists from setlist.fm
and saves them as text files to C:\MMJ-Corpus\04-setlists\
"""

import requests
from bs4 import BeautifulSoup
import time
import os

# ── Config ────────────────────────────────────────────────────
OUTPUT_DIR = r"C:\MMJ-Corpus\04-setlists"
BASE_URL   = "https://www.setlist.fm"
MMJ_URL    = "https://www.setlist.fm/setlists/my-morning-jacket-33d69865.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

MAX_PAGES = 10  # each page has ~15 setlists, 10 pages = ~150 shows

# ── Helpers ───────────────────────────────────────────────────
def fetch_setlist_links(page_url):
    """Get all setlist links from a listing page."""
    r = requests.get(page_url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.select("a.summary.url"):
        href = a.get("href", "")
        if "/setlist/" in href:
            links.append(BASE_URL + href if href.startswith("/") else href)
    return links, soup

def get_next_page(soup):
    """Find the next page URL if it exists."""
    next_btn = soup.select_one("a[rel='next']")
    if next_btn:
        href = next_btn.get("href", "")
        return BASE_URL + href if href.startswith("/") else href
    return None

def fetch_setlist(url):
    """Fetch and parse a single setlist page into clean text."""
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Date and venue
    date = ""
    venue = ""
    city = ""

    date_el = soup.select_one("span.dateBlock")
    if date_el:
        date = date_el.get_text(separator=" ", strip=True)

    venue_el = soup.select_one("h1.setlistHeadline")
    if venue_el:
        venue = venue_el.get_text(separator=" ", strip=True)

    city_el = soup.select_one("a.city")
    if city_el:
        city = city_el.get_text(strip=True)

    # Sets and songs
    lines = [f"Date: {date}", f"Venue: {venue}", f"City: {city}", ""]

    for setblock in soup.select("div.setlistSet"):
        # Set label (Set 1, Encore, etc.)
        label_el = setblock.select_one("div.songLabel")
        if label_el:
            lines.append(f"[{label_el.get_text(strip=True)}]")

        for song in setblock.select("li.song"):
            name_el = song.select_one("a") or song.select_one("span")
            if name_el:
                song_name = name_el.get_text(strip=True)
                # Check for notes (cover, segue, etc.)
                note = song.select_one("span.info")
                note_text = f" ({note.get_text(strip=True)})" if note else ""
                lines.append(f"  - {song_name}{note_text}")

    # Tour info
    tour_el = soup.select_one("a.tour")
    if tour_el:
        lines.append(f"\nTour: {tour_el.get_text(strip=True)}")

    return "\n".join(lines)

def safe_filename(url, date):
    """Generate a safe filename from date and URL."""
    slug = url.rstrip("/").split("/")[-1][:40]
    date_clean = date.replace(" ", "_").replace("/", "-")[:20]
    return f"{date_clean}_{slug}.txt".replace(" ", "_")

# ── Main ──────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  MMJ RAGu Academy — Setlist Scraper")
    print("=" * 55)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    page_url = MMJ_URL
    total_saved = 0
    page_num = 1

    while page_url and page_num <= MAX_PAGES:
        print(f"\nPage {page_num}: {page_url}")
        try:
            links, soup = fetch_setlist_links(page_url)
            print(f"  Found {len(links)} setlists")

            for link in links:
                try:
                    text = fetch_setlist(link)
                    # Extract date for filename
                    date_line = [l for l in text.split("\n") if l.startswith("Date:")]
                    date = date_line[0].replace("Date: ", "") if date_line else "unknown"
                    filename = safe_filename(link, date)
                    filepath = os.path.join(OUTPUT_DIR, filename)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(text)
                    total_saved += 1
                    print(f"  ✓ {filename}")
                    time.sleep(1.5)  # polite delay
                except Exception as e:
                    print(f"  ✗ {link}: {e}")

            page_url = get_next_page(soup)
            page_num += 1
            time.sleep(2)

        except Exception as e:
            print(f"  Page error: {e}")
            break

    print(f"\n{'=' * 55}")
    print(f"  Done! {total_saved} setlists saved to {OUTPUT_DIR}")
    print(f"{'=' * 55}")

if __name__ == "__main__":
    main()
