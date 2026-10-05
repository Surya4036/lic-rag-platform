## Goal

Implement the **Vector Store & Embeddings Pipeline** to generate text embeddings for parsed policy chunks and provide a hybrid vector index supporting both Vertex AI Embeddings + Cloud SQL (pgvector) and a local in-memory/FAISS/Chroma fallback for fast offline development and testing.

## Requirements

1. **Embeddings Pipeline (`src/embeddings/embedder.py`)**:
   - Support `text-embedding-004` (Vertex AI Text Embeddings) as primary.
   - Provide a local fallback (`all-MiniLM-L6-v2` via `sentence-transformers` or mock vector generator) when GCP credentials or Vertex AI API is offline.

2. **Vector Store Interface (`src/vectorstore/store.py`)**:
   - Store chunk embeddings along with full metadata payload (`chunk_id`, `policy_uin`, `policy_name`, `header_path`, `content`, `contains_table`).
   - Support cosine similarity query retrieval with filtering by `policy_uin` or `policy_name`.

3. **Ingestion Script (`scripts/ingest_chunks.py`)**:
   - Load `data/chunks/parsed_chunks.json`.
   - Embed and index all policy chunks.
   - Save vector store index locally to `data/vector_store/` (for local dev) or upload to vector index endpoint.

4. **Verification & Tests (`tests/test_vectorstore.py`)**:
   - Test indexing and query retrieval accuracy on sample policy questions.
