import sys
import os
import json
import pytest
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.embeddings.embedder import PolicyEmbedder
from src.vectorstore.store import VectorStore

def test_embedder_dimension_and_normalization():
    embedder = PolicyEmbedder(force_local=True)
    texts = [
        "LIC Jeevan Umang provides 8% annual survival benefit.",
        "LIC Bima Shree is designed for High Net-worth Individuals."
    ]
    embeddings = embedder.embed_texts(texts)
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 768
    
    # Check norm ~ 1.0 (unit vector)
    norm0 = np.linalg.norm(embeddings[0])
    assert pytest.approx(norm0, 1e-3) == 1.0

def test_vectorstore_indexing_and_search():
    embedder = PolicyEmbedder(force_local=True)
    store = VectorStore()
    
    sample_chunks = [
        {
            "chunk_id": "jeevan-umang-sec-1",
            "policy_uin": "512N312V03",
            "policy_name": "LIC Jeevan Umang",
            "header_path": "LIC Jeevan Umang > Eligibility Conditions",
            "content": "[LIC Jeevan Umang > Eligibility Conditions]\nMinimum Basic Sum Assured: Rs. 2,00,000. Maximum Basic Sum Assured: No limit.",
            "contains_table": False,
            "token_count": 50
        },
        {
            "chunk_id": "bima-shree-sec-1",
            "policy_uin": "512N316V03",
            "policy_name": "LIC Bima Shree",
            "header_path": "LIC Bima Shree > High Networth Individuals",
            "content": "[LIC Bima Shree > Key Features]\nSpecially designed for High Net-worth Individuals. Guaranteed additions accrued annually.",
            "contains_table": False,
            "token_count": 55
        }
    ]
    
    embeddings = embedder.embed_texts([c["content"] for c in sample_chunks])
    store.add_chunks(sample_chunks, embeddings)
    
    # Query search
    q_vector = embedder.embed_query("What is the minimum sum assured for Jeevan Umang?")
    results = store.search(q_vector, top_k=1)
    
    assert len(results) == 1
    assert results[0]["chunk"]["chunk_id"] == "jeevan-umang-sec-1"
    assert results[0]["score"] > 0.0

def test_vectorstore_filtering():
    embedder = PolicyEmbedder(force_local=True)
    store = VectorStore()
    
    sample_chunks = [
        {
            "chunk_id": "c1",
            "policy_uin": "512N312V03",
            "policy_name": "LIC Jeevan Umang",
            "header_path": "LIC Jeevan Umang > Benefits",
            "content": "Survival benefit equal to 8% of Basic Sum Assured.",
            "contains_table": False,
            "token_count": 30
        },
        {
            "chunk_id": "c2",
            "policy_uin": "512N280V03",
            "policy_name": "LIC Money Back 20 Yrs",
            "header_path": "LIC Money Back 20 Yrs > Benefits",
            "content": "Survival benefit of 20% of Basic Sum Assured at end of 5th, 10th, 15th year.",
            "contains_table": False,
            "token_count": 35
        }
    ]
    
    embeddings = embedder.embed_texts([c["content"] for c in sample_chunks])
    store.add_chunks(sample_chunks, embeddings)
    
    q_vector = embedder.embed_query("Survival benefit percentage")
    filtered_results = store.search(q_vector, top_k=5, policy_uin_filter="512N280V03")
    
    assert len(filtered_results) == 1
    assert filtered_results[0]["chunk"]["chunk_id"] == "c2"

def test_vectorstore_persistence(tmp_path):
    embedder = PolicyEmbedder(force_local=True)
    store = VectorStore()
    
    chunk = {
        "chunk_id": "c1",
        "policy_uin": "512N312V03",
        "policy_name": "LIC Jeevan Umang",
        "header_path": "Path",
        "content": "Sample content",
        "contains_table": False,
        "token_count": 10
    }
    emb = embedder.embed_texts([chunk["content"]])
    store.add_chunks([chunk], emb)
    
    save_dir = str(tmp_path / "vector_store")
    store.save(save_dir)
    
    # Load back
    new_store = VectorStore()
    new_store.load(save_dir)
    
    q_vec = embedder.embed_query("Sample")
    res = new_store.search(q_vec, top_k=1)
    
    assert len(res) == 1
    assert res[0]["chunk"]["chunk_id"] == "c1"
