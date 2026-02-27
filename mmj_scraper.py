"""
MMJ Corpus Scraper
Fetches Wikipedia articles and interviews for the MMJ RAG Academy corpus.
Saves clean text files to C:\MMJ-Corpus folder structure.
"""

import requests
from bs4 import BeautifulSoup
import os
import time

# ── Folder paths ──────────────────────────────────────────────
CORPUS_ROOT = r"C:\MMJ-Corpus"
FOLDERS = {
    "wikipedia": os.path.join(CORPUS_ROOT, "01-wikipedia"),
    "interviews": os.path.join(CORPUS_ROOT, "02-interviews"),
}

# ── Wikipedia articles to fetch ───────────────────────────────
WIKIPEDIA_ARTICLES = [
    ("My_Morning_Jacket",           "mmj_main.txt"),
    ("Jim_James",                   "jim_james.txt"),
    ("Carl_Broemel",                "carl_broemel.txt"),
    ("It_Still_Moves",              "it_still_moves.txt"),
    ("Z_(My_Morning_Jacket_album)", "z_album.txt"),
    ("Evil_Urges",                  "evil_urges.txt"),
    ("Circuital",                   "circuital.txt"),
    ("The_Waterfall_(album)",       "the_waterfall.txt"),
    ("The_Waterfall_II",            "the_waterfall_ii.txt"),
    ("My_Morning_Jacket_(album)",   "mmj_album_2021.txt"),
    ("Okonokos",                    "okonokos.txt"),
]

# ── Interviews to fetch ───────────────────────────────────────
# Add paywalled or login-required URLs here as empty string
# and manually save those files to 02-interviews yourself
INTERVIEWS = [
    (
        "https://thequietus.com/interviews/jim-james-interview-my-morning-jacket/",
        "jim_james_regions_of_light_quietus.txt"
    ),
    (
        "https://www.grammy.com/news/my-morning-jacket-interview-jim-james-is-new-album",
        "jim_james_is_album_grammy.txt"
    ),
    (
        "https://sacredmattersmagazine.com/jim-james-musical-blend-of-the-religious-spiritual-and-secular/",
        "jim_james_spirituality_sacred_matters.txt"
    ),
    (
        "https://www.songwritersonprocess.com/blog/2019/5/22/jimjamesmmj",
        "jim_james_songwriting_process.txt"
    ),
    (
        "https://www.grammy.com/news/my-morning-jacket-jim-james-interview-nature-love-existential-new-self-titled-album",
        "jim_james_self_titled_grammy.txt"
    ),
]

# ── Helpers ───────────────────────────────────────────────────
HEADERS = {"User-Agent": "Mozilla/5.0 (MMJ-RAG-Academy-Corpus-Builder)"}

def fetch_wikipedia(article_name):
    """Fetch plain text from Wikipedia via their API."""
    url = f"https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": article_name,
        "prop": "extracts",
        "explaintext": True,
        "format": "json",
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    pages = r.json()["query"]["pages"]
    page = next(iter(pages.values()))
    return page.get("extract", "")

def fetch_article(url):
    """Fetch and clean text from a generic article URL."""
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # Remove nav, footer, ads, scripts
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    # Get all paragraph text
    paragraphs = soup.find_all("p")
    text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    return text

def save_file(folder, filename, content):
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    size_kb = len(content.encode("utf-8")) // 1024
    print(f"  ✓ Saved {filename} ({size_kb} KB)")

# ── Main ──────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  MMJ Corpus Scraper — RAG Academy")
    print("=" * 55)

    # Wikipedia
    print(f"\n[1/2] Fetching {len(WIKIPEDIA_ARTICLES)} Wikipedia articles...")
    for article_name, filename in WIKIPEDIA_ARTICLES:
        try:
            print(f"  Fetching: {article_name}")
            text = fetch_wikipedia(article_name)
            if text:
                save_file(FOLDERS["wikipedia"], filename, text)
            else:
                print(f"  ✗ No content returned for {article_name}")
        except Exception as e:
            print(f"  ✗ Failed {article_name}: {e}")
        time.sleep(1)  # Be polite to Wikipedia

    # Interviews
    print(f"\n[2/2] Fetching {len(INTERVIEWS)} interviews...")
    for url, filename in INTERVIEWS:
        try:
            print(f"  Fetching: {url[:60]}...")
            text = fetch_article(url)
            if text:
                save_file(FOLDERS["interviews"], filename, text)
            else:
                print(f"  ✗ No content for {filename}")
        except Exception as e:
            print(f"  ✗ Failed {filename}: {e}")
        time.sleep(2)

    print("\n" + "=" * 55)
    print("  Done! Check C:\\MMJ-Corpus for your files.")
    print("  Manually add any paywalled interviews to 02-interviews.")
    print("=" * 55)

if __name__ == "__main__":
    main()
