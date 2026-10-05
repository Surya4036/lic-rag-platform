import pytest
from src.vectorstore.pgvector_store import PGVectorStore

def test_pgvector_store_initialization():
    store = PGVectorStore(host="34.100.195.31", user="lic_admin", dbname="lic_rag_db")
    assert store.host == "34.100.195.31"
    assert store.user == "lic_admin"
    assert store.dbname == "lic_rag_db"

def test_pgvector_store_live_search():
    store = PGVectorStore()
    dummy_embedding = [0.01] * 768
    results = store.search(dummy_embedding, top_k=2)
    assert isinstance(results, list)
    if results:
        assert "chunk" in results[0]
        assert "score" in results[0]
