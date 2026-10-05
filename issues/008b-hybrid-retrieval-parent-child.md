## Goal

Refine the chunking and retrieval pipelines to support **Parent-Child Chunking** (Parent ~1000 tokens, Child ~250 tokens with metadata like `min_entry_age`, `max_entry_age`, `riders`) and **Hybrid Retrieval** (Vertex AI Dense Vector Embeddings + BM25 Sparse Keyword Ranking via Reciprocal Rank Fusion).

## Requirements

1. **Parent-Child Chunking (`src/chunking/chunker.py`)**:
   - Generate Parent Chunks representing entire logical sections.
   - Generate Child Chunks (~200–300 tokens) carrying `parent_chunk_id`, section context, and extracted metadata.

2. **BM25 Sparse Search & Hybrid Fusion (`src/vectorstore/store.py`)**:
   - Implement BM25 Keyword Search using TF-IDF / term frequency.
   - Combine Dense Vector scores and BM25 Sparse scores using Reciprocal Rank Fusion (RRF):
     $$\text{RRF Score}(d) = \frac{1}{60 + r_{\text{dense}}(d)} + \frac{1}{60 + r_{\text{bm25}}(d)}$$

3. **Tests (`tests/test_hybrid_retrieval.py`)**:
   - Test BM25 search accuracy on exact keyword queries (e.g. "UIN 512N312V03", "PPT 15 years").
   - Test Parent-Child chunk linking and RRF hybrid retrieval.
