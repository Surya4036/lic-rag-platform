import sys
import os
import json
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.embeddings.embedder import PolicyEmbedder
from src.vectorstore.store import VectorStore

DATA_CHUNKS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chunks", "parsed_chunks.json")
VECTOR_STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vector_store")

def run_ingestion():
    if not os.path.exists(DATA_CHUNKS_PATH):
        print(f"Error: Chunks file not found at '{DATA_CHUNKS_PATH}'. Run chunker first.")
        return

    print(f"Loading policy chunks from '{DATA_CHUNKS_PATH}'...")
    with open(DATA_CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks: List[Dict[str, Any]] = json.load(f)

    print(f"Loaded {len(chunks)} policy chunks.")

    embedder = PolicyEmbedder()
    print("Generating embeddings for policy chunks...")
    texts = [c["content"] for c in chunks]
    embeddings = embedder.embed_texts(texts)

    store = VectorStore()
    store.add_chunks(chunks, embeddings)

    print(f"Saving vector store index to '{VECTOR_STORE_DIR}'...")
    store.save(VECTOR_STORE_DIR)
    print(f"Ingestion complete! Successfully indexed {len(chunks)} chunks in vector store.")

if __name__ == "__main__":
    run_ingestion()
