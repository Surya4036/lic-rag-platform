import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.embeddings.embedder import PolicyEmbedder
from src.vectorstore.store import VectorStore

VECTOR_STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vector_store")

def test_queries():
    store = VectorStore()
    store.load(VECTOR_STORE_DIR)
    embedder = PolicyEmbedder()

    queries = [
        "What is the minimum entry age for LIC Jeevan Umang?",
        "What are the survival benefits in LIC Bima Shree?",
        "Tell me about death benefits and lump sum payment in Money Back 20 years plan"
    ]

    for q in queries:
        print(f"\n--- QUERY: '{q}' ---")
        q_vec = embedder.embed_query(q)
        # Apply filter if query mentions a specific policy
        filter_uin = "512N312V03" if "Jeevan Umang" in q else None
        results = store.search(q_vec, top_k=2, policy_uin_filter=filter_uin)
        for i, res in enumerate(results, 1):
            chunk = res["chunk"]
            score = res["score"]
            print(f"Result #{i} [Score: {score:.4f}]")
            print(f"  Policy: {chunk['policy_name']} (UIN: {chunk['policy_uin']})")
            print(f"  Header Path: {chunk['header_path']}")
            print(f"  Content Snippet: {chunk['content'][:150]}...\n")

if __name__ == "__main__":
    test_queries()
