import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "embeeding"))

from langchain_community.vectorstores import Chroma
from embedding import get_embeddings, load_all_chunks

CHROMA_BASE_DIR = Path(__file__).resolve().parent.parent / "chroma_db"
CHECKPOINT_FILE = Path(__file__).resolve().parent.parent / "embed_checkpoint.json"
BATCH_SIZE = 50


def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {}


def save_checkpoint(checkpoint):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2)


def store_all():
    print("=" * 55)
    print("ChromaDB Store - Ollama + ChromaDB (Batched)")
    print("=" * 55)

    embeddings = get_embeddings()
    CHROMA_BASE_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks = load_all_chunks()
    checkpoint = load_checkpoint()

    for cat_name, chunks in all_chunks.items():
        chroma_path = CHROMA_BASE_DIR / cat_name
        start_batch = checkpoint.get(cat_name, 0)
        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"\n--- {cat_name.upper()} ---")
        print(f"  Total chunks : {len(chunks)}")
        print(f"  Total batches: {total_batches}")
        print(f"  Resuming from batch: {start_batch}")

        vectorstore = Chroma(
            persist_directory=str(chroma_path),
            embedding_function=embeddings,
            collection_name=cat_name,
        )

        for batch_idx in range(start_batch, total_batches):
            start = batch_idx * BATCH_SIZE
            end = min(start + BATCH_SIZE, len(chunks))
            batch = chunks[start:end]

            try:
                vectorstore.add_documents(batch)
                checkpoint[cat_name] = batch_idx + 1
                save_checkpoint(checkpoint)
                print(f"  [OK] Batch {batch_idx + 1}/{total_batches}"
                      f"  (chunks {start}-{end - 1})")
            except Exception as e:
                print(f"  [FAIL] Batch {batch_idx + 1} failed: {e}")
                print("  -> Run again to resume from this batch.")
                return

        print(f"  [Done] {cat_name} complete")

    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

    print("\n" + "=" * 55)
    print("All categories stored in ChromaDB")
    print(f"Location: {CHROMA_BASE_DIR}")
    print("=" * 55)


def search(query, category=None, top_k=5):
    embeddings = get_embeddings()

    if category:
        chroma_path = CHROMA_BASE_DIR / category
        vectorstore = Chroma(
            persist_directory=str(chroma_path),
            embedding_function=embeddings,
            collection_name=category,
        )
        return vectorstore.similarity_search(query, k=top_k)

    results = []
    for cat_path in CHROMA_BASE_DIR.iterdir():
        if not cat_path.is_dir():
            continue
        vectorstore = Chroma(
            persist_directory=str(cat_path),
            embedding_function=embeddings,
            collection_name=cat_path.name,
        )
        results.extend(vectorstore.similarity_search(query, k=top_k))
    return results


if __name__ == "__main__":
    store_all()

    results = search("What are the symptoms of acne?", category="skin_disease")
    print("\nRESULTS\n")
    for i, doc in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print("Disease:", doc.metadata.get("disease"))
        print("Category:", doc.metadata.get("category"))
        print("Source:", doc.metadata.get("source"))
        print(doc.page_content[:500])