"""
MMJ RAGu Academy — Ingestion Pipeline (Voyage-3 Embeddings)
Reads corpus files, chunks them, embeds with voyageai voyage-3,
and stores in LanceDB for retrieval.
Run this once (or whenever corpus changes).
"""

import os
import sys
import glob
import time
import lancedb
import voyageai

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Config ────────────────────────────────────────────────────
CORPUS_ROOT   = r"C:\MMJ-Corpus"
LANCE_PATH    = r"C:\MMJ-Corpus\lance_db"
TABLE_NAME    = "mmj_corpus"
CHUNK_SIZE    = 500
CHUNK_OVERLAP = 50
EMBED_MODEL   = "voyage-3"
BATCH_SIZE    = 8

INGEST_FOLDERS = [
    "01-wikipedia",
    "02-interviews",
    "03-reviews",
    "04-setlists",
    "05-albums",
    "07-social",
    "08-john-kean",
]

LINE_CHUNK_FOLDERS = {"04-setlists"}

# ── Chunkers ─────────────────────────────────────────────────
def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def chunk_by_lines(text, lines_per_chunk=20):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    chunks = []
    for i in range(0, len(lines), lines_per_chunk):
        chunk = "\n".join(lines[i:i + lines_per_chunk])
        if chunk:
            chunks.append(chunk)
    return chunks

# ── Embedder ─────────────────────────────────────────────────
def embed_texts(vo_client, texts):
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        result = vo_client.embed(batch, model=EMBED_MODEL, input_type="document")
        all_embeddings.extend(result.embeddings)
        print(f"    Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)} chunks...")
        time.sleep(0.3)
    return all_embeddings

# ── Main ──────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  MMJ RAGu Academy — Ingestion Pipeline (voyage-3)")
    print("=" * 55)

    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        raise ValueError("VOYAGE_API_KEY environment variable not set")

    vo_client = voyageai.Client(api_key=api_key)
    print("\nVoyage AI client ready.")

    print(f"\nConnecting to LanceDB at {LANCE_PATH}...")
    db = lancedb.connect(LANCE_PATH)

    # Unconditional drop — try/except handles case where table doesn't exist
    try:
        db.drop_table(TABLE_NAME)
        print("  Cleared existing table.")
    except Exception:
        print("  No existing table to clear.")

    all_records = []
    total_files = 0

    for folder in INGEST_FOLDERS:
        folder_path = os.path.join(CORPUS_ROOT, folder)
        # recursive=True picks up all subfolders (e.g. 04-setlists\official\)
        files = glob.glob(os.path.join(folder_path, "**", "*.txt"), recursive=True)

        if not files:
            print(f"\n  [{folder}] — no files found, skipping")
            continue

        use_line_chunks = folder in LINE_CHUNK_FOLDERS
        mode = "line-chunked" if use_line_chunks else "word-chunked"
        print(f"\n  [{folder}] — {len(files)} files ({mode})")

        for filepath in files:
            filename = os.path.basename(filepath)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read().strip()

                if not text:
                    print(f"    ✗ {filename} — empty, skipping")
                    continue

                chunks = chunk_by_lines(text) if use_line_chunks else chunk_text(text)

                if not chunks:
                    continue

                for i, chunk in enumerate(chunks):
                    all_records.append({
                        "id":       f"{folder}__{filename}__chunk_{i}",
                        "text":     chunk,
                        "source":   filename,
                        "folder":   folder,
                        "chunk_id": i,
                    })

                total_files += 1
                print(f"    ✓ {filename} — {len(chunks)} chunks")

            except Exception as e:
                print(f"    ✗ {filename} — {e}")

    if not all_records:
        print("\nNo records to embed. Check your corpus folders.")
        return

    total_chunks = len(all_records)
    print(f"\nEmbedding {total_chunks} chunks with {EMBED_MODEL}...")
    texts = [r["text"] for r in all_records]
    embeddings = embed_texts(vo_client, texts)

    print("\nWriting to LanceDB...")
    records = [
        {
            "id":       r["id"],
            "text":     r["text"],
            "source":   r["source"],
            "folder":   r["folder"],
            "chunk_id": r["chunk_id"],
            "vector":   embeddings[i],
        }
        for i, r in enumerate(all_records)
    ]

    # mode="overwrite" as safety net in case drop didn't fully clear
    db.create_table(TABLE_NAME, data=records, mode="overwrite")

    print(f"\n{'=' * 55}")
    print(f"  Done! {total_files} files → {total_chunks} chunks embedded.")
    print(f"  Model: {EMBED_MODEL} | DB: {LANCE_PATH}")
    print(f"{'=' * 55}")

if __name__ == "__main__":
    main()
