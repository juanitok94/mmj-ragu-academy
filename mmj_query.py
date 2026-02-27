"""
MMJ RAGu Academy — Query Engine
Takes a question, searches LanceDB for relevant chunks,
sends context to Claude, returns a grounded answer.
"""

import os
import anthropic
import lancedb
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────
LANCE_PATH   = r"C:\MMJ-Corpus\lance_db"
TABLE_NAME   = "mmj_corpus"
EMBED_MODEL  = "all-MiniLM-L6-v2"
TOP_K        = 15
MODEL        = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a friendly, knowledgeable expert on My Morning Jacket, 
the band from Louisville, Kentucky. You're like a fellow superfan who happens to 
know everything about the band.

Answer questions conversationally and warmly. Use the provided context as your 
primary source for MMJ-specific facts like setlist data, play counts, and band history.

You may use general music knowledge (like whether a song is a cover or who originally 
recorded it) to supplement the context.

When something isn't in your context, say so naturally — like "I don't have that in 
my notes" or "that one's not showing up for me" rather than formal disclaimers. 
Keep it conversational, like you're chatting with a fellow fan.

Never invent MMJ-specific facts that aren't in the provided context."""

# ── Setup ─────────────────────────────────────────────────────
print("Loading MMJ RAGu Academy...")
model  = SentenceTransformer(EMBED_MODEL)
db     = lancedb.connect(LANCE_PATH)
table  = db.open_table(TABLE_NAME)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
print("Ready.\n")

# ── Query function ────────────────────────────────────────────
def ask(question: str) -> str:
    # Primary vector search
    query_vector = model.encode(question).tolist()
    results = table.search(query_vector).limit(TOP_K).to_list()

    # Keyword boost — if question contains a song name, also search by keyword
    question_lower = question.lower()
    keyword_results = []
    try:
        all_rows = table.search(query_vector).limit(200).to_list()
        for row in all_rows:
            # Check if any word from question appears in chunk text
            words = [w for w in question_lower.split() if len(w) > 3]
            if any(w in row['text'].lower() for w in words):
                if row['id'] not in {r['id'] for r in results}:
                    keyword_results.append(row)
                    if len(keyword_results) >= 5:
                        break
    except Exception:
        pass

    combined = results + keyword_results
    if not combined:
        return "Hmm, I don't have anything on that in my notes. Try asking it a different way?"

    context_parts = []
    for r in combined:
        context_parts.append(f"[Source: {r['source']}]\n{r['text']}")
    context = "\n\n---\n\n".join(context_parts)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            }
        ]
    )
    return response.content[0].text

# ── Interactive loop ──────────────────────────────────────────
def main():
    print("=" * 55)
    print("  MMJ RAGu Academy — Ask Anything")
    print("  Type 'quit' to exit")
    print("=" * 55)
    print()

    while True:
        question = input("Your question: ").strip()
        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Later!")
            break

        print("\nSearching corpus and asking Claude...\n")
        answer = ask(question)
        print(f"Answer:\n{answer}")
        print("\n" + "-" * 55 + "\n")

if __name__ == "__main__":
    main()
