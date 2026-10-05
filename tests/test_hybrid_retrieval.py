import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.embeddings.embedder import PolicyEmbedder
from src.vectorstore.store import VectorStore

def test_bm25_and_hybrid_search():
    embedder = PolicyEmbedder(force_local=True)
    store = VectorStore()
    
    sample_chunks = [
        {
            "chunk_id": "c1",
            "parent_chunk_id": "parent-1",
            "policy_uin": "512N312V03",
            "policy_name": "LIC Jeevan Umang",
            "header_path": "LIC Jeevan Umang > Eligibility",
            "content": "[LIC Jeevan Umang > Eligibility] Minimum basic sum assured is Rs. 200,000 for UIN 512N312V03.",
            "contains_table": False,
            "token_count": 30
        },
        {
            "chunk_id": "c2",
            "parent_chunk_id": "parent-2",
            "policy_uin": "512N316V03",
            "policy_name": "LIC Bima Shree",
            "header_path": "LIC Bima Shree > High Networth",
            "content": "[LIC Bima Shree > Key Features] Designed for High Net-worth Individuals with guaranteed additions.",
            "contains_table": False,
            "token_count": 35
        }
    ]
    
    embeddings = embedder.embed_texts([c["content"] for c in sample_chunks])
    store.add_chunks(sample_chunks, embeddings)
    
    # BM25 Keyword match test
    bm25_res = store.bm25_search("512N312V03")
    assert len(bm25_res) > 0
    assert bm25_res[0]["chunk"]["chunk_id"] == "c1"
    
    # Hybrid search test
    q_vec = embedder.embed_query("UIN 512N312V03 minimum sum assured")
    hybrid_res = store.hybrid_search("UIN 512N312V03 minimum sum assured", q_vec, top_k=1)
    
    assert len(hybrid_res) == 1
    assert hybrid_res[0]["chunk"]["chunk_id"] == "c1"
    assert "rrf_score" in hybrid_res[0]
