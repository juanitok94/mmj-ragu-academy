"""
MMJ RAGu Academy — Official Archive Scraper
Scrapes My Morning Jacket setlists from archive.mymorningjacket.net
(the official band-maintained archive, 1999-2025, ~1,300 shows)
Saves clean text files to C:\MMJ-Corpus\04-setlists\

Run after clearing existing setlist.fm files, or into a separate
subfolder like 04-setlists\official\ to keep sources distinct.

Usage:
    python mmj_archive_scraper.py
    python mmj_archive_scraper.py --years 2022 2023 2024  # specific years only
    python mmj_archive_scraper.py --output C:\MMJ-Corpus\04-setlists\official
"""

import requests
from bs4 import BeautifulSoup
import time
import os
import argparse
import re

# ── Config ────────────────────────────────────────────────────
BASE_URL   = "https://archive.mymorningjacket.net"
OUTPUT_DIR = r"C:\MMJ-Corpus\04-setlists"
DELAY      = 1.5   # seconds between requests — be polite

HEADERS = {
    "User-Agent": "Mozilla/5.0 (MMJ-RAGu-Academy-Corpus-Builder; respectful scraper)",
}

# All years with known shows
ALL_YEARS = [
    1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008,
    2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018,
    2019, 2021, 2022, 2023, 2024, 2025,
]

# ── Helpers ───────────────────────────────────────────────────
def get_year_url(year):
    """Year index URL pattern from the archive."""
    return f"{BASE_URL}/index.php/shows/{year}-shows"

def fetch_show_links(year):
    """Get all show page links and titles from a year index page."""
    url = get_year_url(year)
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    shows = []
    # Show links are <a> tags inside the article list
    for a in soup.select("table a, td a, .items a, a"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        # Show titles follow pattern: YYYY-MM-DD Venue - City, State
        if href and re.match(r"\d{4}-\d{2}-\d{2}", text):
            full_url = BASE_URL + href if href.startswith("/") else href
            shows.append((text, full_url))

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for title, url in shows:
        if url not in seen:
            seen.add(url)
            unique.append((title, url))

    return unique

def fetch_show(title, url):
    """Fetch and parse a single show page into clean text."""
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Parse date and venue from title: "YYYY-MM-DD Venue - City, State"
    date = title[:10] if len(title) >= 10 else "unknown"
    venue_info = title[11:] if len(title) > 11 else title

    lines = [
        f"Date: {date}",
        f"Venue: {venue_info}",
        "",
    ]

    # Get main content area — strip nav, footer, search
    for tag in soup(["nav", "footer", "header", "script", "style"]):
        tag.decompose()

    # Remove sidebar/nav links
    for tag in soup.select(".nav, .sidebar, #search, .search"):
        tag.decompose()

    # Get all text lines from the main article body
    # Songs appear as plain text lines in the content area
    content = soup.get_text(separator="\n")
    content_lines = [l.strip() for l in content.split("\n") if l.strip()]

    # Extract setlist — starts after venue info, ends at "poster by" or nav items
    in_setlist = False
    set_label = "Set:"
    song_lines = []

    for line in content_lines:
        # Skip navigation and boilerplate
        if any(skip in line for skip in [
            "SEARCH LIVE ARCHIVE", "LIVE ARCHIVE", "Back to Top",
            "MY MORNING JACKET", "© 20", "• HOME", "• SHOWS",
            "• FORUM", "• STORE", "UPCOMING", "STREAMS", "Title Filter",
            "Display #", "Articles", "Next article", "Previous article",
            "My Morning Jacket Live Archive", "Search",
        ]):
            continue

        # "poster by" line signals end of setlist
        if line.lower().startswith("poster by") or line.lower().startswith("by "):
            break

        # ---------- signals encore break
        if line.startswith("---"):
            song_lines.append("--- Encore ---")
            continue

        # Skip the title line (it repeats the date/venue)
        if line == title:
            in_setlist = True
            continue

        if in_setlist and line:
            song_lines.append(line)
        elif not in_setlist and line:
            # Try to detect start of setlist (first song after venue)
            # Heuristic: line doesn't contain common nav words
            in_setlist = True
            song_lines.append(line)

    if song_lines:
        lines.append("Setlist:")
        lines.extend(f"  {s}" for s in song_lines)
    else:
        lines.append("(setlist not parsed)")

    return "\n".join(lines)

def safe_filename(title):
    """Generate a safe filename from show title."""
    # Title format: "YYYY-MM-DD Venue - City, State"
    clean = re.sub(r'[<>:"/\\|?*]', '', title)
    clean = clean.replace(" ", "_")[:80]
    return f"{clean}.txt"

# ── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="MMJ Official Archive Scraper")
    parser.add_argument("--years", nargs="+", type=int, help="Specific years to scrape")
    parser.add_argument("--output", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    years = args.years if args.years else ALL_YEARS
    output_dir = args.output

    print("=" * 60)
    print("  MMJ RAGu Academy — Official Archive Scraper")
    print(f"  Source: archive.mymorningjacket.net")
    print(f"  Years:  {min(years)} – {max(years)}")
    print(f"  Output: {output_dir}")
    print("=" * 60)

    os.makedirs(output_dir, exist_ok=True)

    total_saved = 0
    total_errors = 0

    for year in sorted(years):
        print(f"\n[{year}] Fetching show list...")
        try:
            shows = fetch_show_links(year)
            print(f"  Found {len(shows)} shows")

            if not shows:
                print(f"  ⚠ No shows found for {year} — check URL pattern")
                continue

            for title, url in shows:
                filename = safe_filename(title)
                filepath = os.path.join(output_dir, filename)

                # Skip if already scraped
                if os.path.exists(filepath):
                    print(f"  → skip (exists): {filename}")
                    continue

                try:
                    text = fetch_show(title, url)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(text)
                    total_saved += 1
                    print(f"  ✓ {filename}")
                    time.sleep(DELAY)

                except Exception as e:
                    total_errors += 1
                    print(f"  ✗ {title}: {e}")

            time.sleep(DELAY)

        except Exception as e:
            print(f"  ✗ Year {year} index failed: {e}")
            total_errors += 1

    print(f"\n{'=' * 60}")
    print(f"  Done! {total_saved} shows saved, {total_errors} errors")
    print(f"  Output: {output_dir}")
    print(f"  Next: run mmj_ingest.py to re-embed and commit lance_db/")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
