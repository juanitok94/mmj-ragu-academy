---
name: mmj-ragu-academy
description: Project knowledge base for MMJ RAGu Academy — a production RAG system built on FastAPI + LanceDB + Voyage-3 + Claude Haiku. Use this skill whenever working on any part of this codebase: backend API, ingestion pipeline, frontend, deployment, corpus management, or scraping. Trigger on any mention of mmj_api, lance_db, RAGu, ingest, setlists, Voyage, Render deploy, Vercel frontend, corpus, or Snow Strippers clone for this project.
---

# MMJ RAGu Academy — Project SKILL

A full-stack RAG (Retrieval-Augmented Generation) system for My Morning Jacket superfans.
Built by John Kean / Peachy Kean DevOps LLC. February–March 2026.

- **Live frontend:** https://mmj-ragu-academy.vercel.app
- **Backend API:** https://mmj-ragu-academy.onrender.com (health check: `/health`)
- **Repo:** https://github.com/juanitok94/mmj-ragu-academy (public, `main` only)

---

## Stack

| Layer | Technology | Notes |
|---|---|---|
| LLM | `claude-haiku-4-5-20251001` | Switched from Sonnet — sufficient for factual Q&A with context |
| Embeddings | Voyage AI `voyage-3` | Switched from `sentence-transformers/all-MiniLM-L6-v2` |
| Vector DB | LanceDB 0.29.2 | Switched from ChromaDB — incompatible with Python 3.14 |
| Backend | FastAPI + uvicorn | `mmj_api.py` — deployed on Render |
| Frontend | Next.js 15 + Tailwind | Deployed on Vercel, retro FF7 aesthetic |
| Corpus | `.txt` files | `C:\MMJ-Corpus\` locally, `lance_db/` committed to Git (0.6MB) |
| Python (local) | 3.14.3 | Note: 3.14 broke ChromaDB, LanceDB has no version restrictions |
| Node/npm | see `web/package.json` | Run `cd web && npm install` before first local frontend run |

---

## Critical History — Do Not Undo These Decisions

- **ChromaDB is banned.** Incompatible with Python 3.14, no fix available. LanceDB is the replacement.
- **sentence-transformers is legacy.** `mmj_query.py` still uses it — that file is the OLD query engine. Do not use in production. `mmj_api.py` is production and uses Voyage-3.
- **Haiku over Sonnet.** Factual Q&A with pre-loaded context doesn't need Sonnet's reasoning depth. Haiku is ~20x cheaper, fast enough for chat UX.
- **LanceDB committed to Git.** The `lance_db/` folder (0.6MB) is committed directly to the repo. It was previously gitignored — that line has been removed from `.gitignore`. Do not re-add it.
- **voyageai is unpinned in requirements.txt.** Was `voyageai==0.3.2` — incompatible with Python 3.13+ on Render. Now just `voyageai` (no version pin).
- **No lyrics in corpus.** Folder `06-lyrics` is intentionally empty — Claude handles lyrics from training data/web search via Render backend. Do not ingest copyrighted lyrics.
- **ANTHROPIC_API_KEY belongs on Render only.** Verified via git history that `route.ts` never called Anthropic directly. Do not add it to Vercel.

---

## Tone & Persona

System prompt uses **restrained personality** — knowledgeable friend, not customer service bot.
- No filler openers ("Great question", "Absolutely!", "Sure!")
- No overuse of "in my notes" — say it once at most, then just answer naturally
- Natural phrasing, fan energy used sparingly
- Hedging only when factually appropriate

---

## File Map

### Python Backend (repo root)
| File | Purpose |
|---|---|
| `mmj_api.py` | Production FastAPI backend — only backend file that matters for deployment |
| `mmj_ingest.py` | Re-ingestion pipeline — run locally when corpus changes, commit updated `lance_db/` |
| `mmj_archive_scraper.py` | Official MMJ archive scraper — `archive.mymorningjacket.net` (1,300 shows, 1999-2025) |
| `mmj_scraper.py` | Wikipedia + interview scraper for corpus acquisition |
| `mmj_albums_scraper.py` | Album track listing scraper (Wikipedia HTML) |
| `mmj_setlist_scraper.py` | Old setlist.fm scraper — superseded by `mmj_archive_scraper.py` |
| `mmj_query.py` | Legacy CLI query tool using sentence-transformers — do not use in production |
| `mmj_missing_albums.py` | Scraper for albums missing from initial run |
| `requirements.txt` | Python deps for Render — voyageai unpinned for Python 3.13+ compat |
| `render.yaml` | Render service config (Blueprint) |
| `SKILL.md` | This file |

### Corpus Folders (local only, not in Git except `lance_db/`)
| Folder | Content | Chunking | Status |
|---|---|---|---|
| `01-wikipedia/` | Band/album Wikipedia articles | Word-chunked (500w, 50 overlap) | Ingested |
| `02-interviews/` | Jim James interviews | Word-chunked | Ingested |
| `03-reviews/` | Album reviews | Word-chunked | Ingested |
| `04-setlists/official/` | Official archive shows (1999-2025) | Line-chunked (20 lines/chunk) | Scraped Mar 2026 |
| `05-albums/` | Track listings with writers/durations | Word-chunked | Ingested |
| `06-lyrics/` | Intentionally empty | — | Do not populate |
| `07-social/` | Social media content | TBD | Placeholder |
| `08-john-kean/` | John Kean biographical notes | Word-chunked | Ingested |

### Next.js Frontend (`web/`)
| File | Purpose |
|---|---|
| `web/app/api/ask/route.ts` | API route — proxies to FastAPI via `NEXT_PUBLIC_API_URL` env var |
| `web/app/page.tsx` | Main chat page |
| `web/tailwind.config.ts` | Custom colors: `bg`, `primary`, `accent`, `input-bg` + pixel font |
| `web/package.json` | Next 15, React 19, Tailwind 3 |

---

## Environment Variables

| Variable | Where set | Value |
|---|---|---|
| `ANTHROPIC_API_KEY` | Render dashboard (secret, sync:false) | Anthropic API key |
| `VOYAGE_API_KEY` | Render dashboard (secret, sync:false) | Voyage AI API key |
| `LANCE_PATH` | Render dashboard (sync:false) | `./lance_db` |
| `NEXT_PUBLIC_API_URL` | Vercel dashboard | `https://mmj-ragu-academy.onrender.com` |

Manage keys at: console.anthropic.com / dash.voyageai.com

---

## Render Deployment (from Blueprint, exported 2026-03-03)

```yaml
service: mmj-ragu-academy
runtime: python
region: virginia
plan: starter
repo: https://github.com/juanitok94/mmj-ragu-academy
buildCommand: pip install -r requirements.txt
startCommand: uvicorn mmj_api:app --host 0.0.0.0 --port $PORT
healthCheckPath: /health
autoDeployTrigger: commit
```

Every git push to main triggers automatic Render redeploy.

---

## Vercel Deployment

```
Project: mmj-ragu-academy
Root directory: web/
Branch: main
Framework: Next.js (auto-detected)
Domain: mmj-ragu-academy.vercel.app
Env vars: NEXT_PUBLIC_API_URL only
Auto-deploy: yes, on every push to main
```

---

## Local Dev Startup

**Backend:**
```powershell
$env:ANTHROPIC_API_KEY="sk-..."
$env:VOYAGE_API_KEY="pa-..."
$env:LANCE_PATH="C:\MMJ-Corpus\lance_db"
cd C:\MMJ-Corpus
uvicorn mmj_api:app --reload --port 8000
```

**Frontend:**
```powershell
cd C:\MMJ-Corpus\web
npm install    # first time only
npm run dev    # runs on localhost:3000
```

For local frontend to hit local backend, set `web/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Re-ingestion Workflow (when corpus changes)

```powershell
# 1. Scrape new content
python mmj_archive_scraper.py --output C:\MMJ-Corpus\04-setlists\official

# 2. Re-embed everything
python mmj_ingest.py

# 3. Commit updated DB
git add lance_db/
git commit -m "corpus: update setlists, re-embed"
git push
# Render and Vercel both auto-redeploy
```

---

## Query Architecture

```
User question
  -> Voyage-3 embed (query mode)
  -> LanceDB vector search (Top-K=15, cosine similarity)
  -> Keyword boost: scan top 200 results for exact word matches, append up to 5
  -> Combined context (up to 20 chunks) -> Claude Haiku
  -> Conversational answer
```

---

## Corpus Sources

| Source | URL | Method | Status |
|---|---|---|---|
| Official setlist archive | archive.mymorningjacket.net | `mmj_archive_scraper.py` | Mar 2026 |
| Wikipedia | en.wikipedia.org/w/api.php | `mmj_scraper.py` | Done |
| Interviews | Various | `mmj_scraper.py` | Done |
| setlist.fm | setlist.fm | `mmj_setlist_scraper.py` | Superseded |
| Official site | mymorningjacket.com | Not yet scraped | Pending |
| Forum | forum.mymorningjacket.net | Not yet scraped | Next session |
| ONE BIG FAMILY | onebigfamily.mymorningjacket.com | Login required | Locked |
| Nugs.net | nugs.net | Show metadata possible | Pending |

---

## Render Cold Start Warning

Starter tier may spin down after inactivity. First request after spindown takes ~30 seconds.
Users may think the app is broken — consider keep-alive ping or frontend warning.

---

## Next Sessions

### 1. Forum Corpus
- `forum.mymorningjacket.net` — fan discussion, deep MMJ knowledge
- Check if publicly scrapable without login
- Add to `07-social/` or new `09-forum/` folder

### 2. Snow Strippers Clone
- Separate GitHub repo, cloned from MMJ as template
- Add `band: string` field to LanceDB schema (`"mmj"` or `"snow_strippers"`)
- API accepts `band` parameter, filters with `.where("band = 'X'")`
- One ingest pipeline with `--band` flag
- Separate Vercel frontend with its own env vars
- Decisions needed: corpus sources, DJ member context

---

## Known Issues

### Typewriter Race Condition (Frontend)
- **File:** `web/app/.../ChatMessage.tsx`
- **Bug:** `prev + chars[index]` in `setInterval` — stale React closure
- **Fix:** Use a `ref` for the index, or `useEffect` with chunk index dependency

### CORS
- Currently `allow_origins=["*"]` in `mmj_api.py`
- Tighten to: `allow_origins=["https://mmj-ragu-academy.vercel.app"]`

### .gitignore Current State
- Ignored: `__pycache__/`, `*.py[cod]`, `*.pyo`, `.env`, `web/node_modules/`, `web/.next/`, `web/.env.local`, `api_key.txt`, `.DS_Store`, `Thumbs.db`
- NOT ignored: `lance_db/` — commit the DB directly
