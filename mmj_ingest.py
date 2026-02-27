"""
MMJ RAGu Academy — Ingestion Pipeline (LanceDB version)
Reads corpus files, chunks them, embeds with sentence-transformers,
and stores in LanceDB for retrieval.
Run this once (or whenever corpus changes).
"""

import os
import glob
import lancedb
import pyarrow as pa
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────
CORPUS_ROOT   = r"C:\MMJ-Corpus"
LANCE_PATH    = r"C:\MMJ-Corpus\lance_db"
TABLE_NAME    = "mmj_corpus"
CHUNK_SIZE    = 500   # words per chunk (default)
CHUNK_OVERLAP = 50    # words overlap between chunks
EMBED_MODEL   = "all-MiniLM-L6-v2"

# Folders to ingest
INGEST_FOLDERS = [
    "01-wikipedia",
    "02-interviews",
    "03-reviews",
    "04-setlists",
    "05-albums",
    "08-john-kean",
]

# Folders that need line-by-line chunking instead of word chunking
LINE_CHUNK_FOLDERS = {"04-setlists"}

# ── Chunkers ─────────────────────────────────────────────────
def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Standard word-based chunking with overlap."""
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
    """
    Line-based chunking for structured data like song stats.
    Groups lines into small chunks so individual songs are retrievable.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    chunks = []
    for i in range(0, len(lines), lines_per_chunk):
        chunk = "\n".join(lines[i:i + lines_per_chunk])
        if chunk:
            chunks.append(chunk)
    return chunks

# ── Main ──────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  MMJ RAGu Academy — Ingestion Pipeline (LanceDB)")
    print("=" * 55)

    print(f"\nLoading embedding model: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)
    print("  Model ready.")

    print(f"\nConnecting to LanceDB at {LANCE_PATH}...")
    db = lancedb.connect(LANCE_PATH)

    if TABLE_NAME in db.list_tables():
        db.drop_table(TABLE_NAME)
        print("  Cleared existing table.")

    all_records = []
    total_files = 0

    for folder in INGEST_FOLDERS:
        folder_path = os.path.join(CORPUS_ROOT, folder)
        files = glob.glob(os.path.join(folder_path, "*.txt"))

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

                if use_line_chunks:
                    chunks = chunk_by_lines(text, lines_per_chunk=20)
                else:
                    chunks = chunk_text(text)

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
    print(f"\nEmbedding {total_chunks} chunks...")
    texts = [r["text"] for r in all_records]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    print("\nWriting to LanceDB...")
    records = []
    for i, record in enumerate(all_records):
        records.append({
            "id":       record["id"],
            "text":     record["text"],
            "source":   record["source"],
            "folder":   record["folder"],
            "chunk_id": record["chunk_id"],
            "vector":   embeddings[i].tolist(),
        })

    db.create_table(TABLE_NAME, data=records)

    print(f"\n{'=' * 55}")
    print(f"  Done! {total_files} files → {total_chunks} chunks embedded.")
    print(f"  Database: {LANCE_PATH}")
    print(f"{'=' * 55}")

if __name__ == "__main__":
    main()
