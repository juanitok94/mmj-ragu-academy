"""
MMJ RAGu Academy — Album Track Listing Scraper (fixed)
Fetches full track listings for all MMJ albums from Wikipedia
and saves to C:\MMJ-Corpus\05-albums\
"""

import requests
from bs4 import BeautifulSoup
import time
import os
import re

OUTPUT_DIR = r"C:\MMJ-Corpus\05-albums"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

ALBUMS = [
    ("the_tennessee_fire", "https://en.wikipedia.org/wiki/The_Tennessee_Fire"),
    ("at_dawn",            "https://en.wikipedia.org/wiki/At_Dawn_(album)"),
    ("it_still_moves",     "https://en.wikipedia.org/wiki/It_Still_Moves"),
    ("z_album",            "https://en.wikipedia.org/wiki/Z_(My_Morning_Jacket_album)"),
    ("evil_urges",         "https://en.wikipedia.org/wiki/Evil_Urges"),
    ("circuital",          "https://en.wikipedia.org/wiki/Circuital"),
    ("the_waterfall",      "https://en.wikipedia.org/wiki/The_Waterfall_(album)"),
    ("the_waterfall_ii",   "https://en.wikipedia.org/wiki/The_Waterfall_II"),
    ("mmj_2021",           "https://en.wikipedia.org/wiki/My_Morning_Jacket_(album)"),
]

def fetch_album(name, url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    lines = []

    # Album title
    title = soup.select_one("h1#firstHeading")
    if title:
        lines.append(f"Album: {title.get_text(strip=True)}")
        lines.append("")

    # Infobox metadata
    infobox = soup.select_one("table.infobox")
    if infobox:
        for row in infobox.select("tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td:
                key = th.get_text(strip=True)
                val = td.get_text(separator=" ", strip=True)
                if key in ("Released", "Recorded", "Genre", "Label", "Producer"):
                    lines.append(f"{key}: {val}")
        lines.append("")

    # Track listings — Wikipedia uses divs with class containing 'tracklist'
    # or ordered lists after track listing headers
    track_sections = soup.find_all("div", class_=re.compile(r"tracklist", re.I))
    
    if track_sections:
        lines.append("Track Listing:")
        for section in track_sections:
            # Section title
            title_el = section.select_one("caption, .tracklist-title")
            if title_el:
                lines.append(f"\n{title_el.get_text(strip=True)}")
            # Tracks as table rows
            for row in section.select("tr"):
                cells = [td.get_text(separator=" ", strip=True) for td in row.select("td")]
                cells = [c for c in cells if c]
                if cells:
                    lines.append("  " + " | ".join(cells))
    else:
        # Fallback: find ordered lists after "Track listing" headers
        for header in soup.find_all(["h2", "h3", "h4"]):
            if "track" in header.get_text(strip=True).lower():
                lines.append(f"\n{header.get_text(strip=True)}:")
                nxt = header.find_next_sibling()
                while nxt and nxt.name not in ["h2", "h3"]:
                    if nxt.name == "ol":
                        for i, li in enumerate(nxt.find_all("li"), 1):
                            lines.append(f"  {i}. {li.get_text(separator=' ', strip=True)}")
                    elif nxt.name == "table":
                        for row in nxt.select("tr"):
                            cells = [td.get_text(separator=" ", strip=True) for td in row.select("td")]
                            cells = [c for c in cells if c]
                            if cells:
                                lines.append("  " + " | ".join(cells))
                    nxt = nxt.find_next_sibling()

    # Last resort: get all li elements near "track" sections
    if len(lines) < 5:
        lines.append("\nAll tracks found on page:")
        for ol in soup.find_all("ol"):
            prev = ol.find_previous(["h2","h3","h4"])
            if prev and "track" in prev.get_text(strip=True).lower():
                for i, li in enumerate(ol.find_all("li"), 1):
                    lines.append(f"  {i}. {li.get_text(separator=' ', strip=True)}")

    return "\n".join(lines)

def main():
    print("=" * 55)
    print("  MMJ RAGu Academy — Album Track Listing Scraper")
    print("=" * 55)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    saved = 0

    for name, url in ALBUMS:
        print(f"\n  Fetching: {name}")
        try:
            text = fetch_album(name, url)
            filepath = os.path.join(OUTPUT_DIR, f"{name}.txt")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            size = len(text)
            status = "✓" if size > 500 else "⚠ (small - may be incomplete)"
            print(f"  {status} {name}.txt — {size:,} chars")
            saved += 1
            time.sleep(1)
        except Exception as e:
            print(f"  ✗ {name} — {e}")

    print(f"\n{'=' * 55}")
    print(f"  Done! {saved} albums saved to {OUTPUT_DIR}")
    print(f"{'=' * 55}")

if __name__ == "__main__":
    main()
