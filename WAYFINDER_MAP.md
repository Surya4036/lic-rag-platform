## Destination

A production-ready Enterprise-Grade AI Assistant and Multi-Modal RAG Platform for LIC policies, deployed on GCP using Cloud Run, Vertex AI, and Cloud SQL, capable of exact premium/payout calculations and document comparisons.

## Notes

- Domain: Life Insurance (LIC policies, premiums, riders, bonuses).
- Architecture: GCP (Cloud Run, Vertex AI Vector Search, Cloud SQL + pgvector, Gemini 1.5/2.0, Cloud Storage).
- Budget: Strictly under ₹26,000 with budget alerts.
- Applicable Skills: `prototype`, `tdd`, `implement`, `diagnosing-bugs`.

## Decisions so far

- **Math Tool Architecture**: Mathematical calculations (bonuses, payouts) will be deterministic. We will create specific Python functions containing the hardcoded bonus tables/values. The LLM will only act as a router to extract parameters (age, term, sum assured) and call the Python tool, rather than attempting to calculate the math itself.
- **GCP Environment**: The GCP project is created and authenticated locally. Region set to `asia-south1` (Mumbai).
- **[Ticket 1: Finalize GCP Resource Naming Conventions and Region](issues/001-gcp-naming-region.md)**: Selected `asia-south1` (Mumbai) as default region. Naming convention: `lic-rag-<resource>-prod`.
- **[Ticket 2: Prototype the LIC Math Payout Tool](issues/002-prototype-math-tool.md)**: Prototyped in `prototypes/math_tool.py`. Confirmed the LLM parameter extraction + deterministic Python execution pattern successfully calculates accurate maturity benefits.
- **[Ticket 3: Determine PDF Parsing Strategy](issues/003-pdf-parsing-strategy.md)**: Benchmarked PyMuPDF4LLM on LIC brochure PDFs. Selected `pymupdf4llm` for local layout-aware markdown table extraction without API cost.
- **[Ticket 4: Determine Data Sourcing Strategy](issues/004-data-sourcing-strategy.md)**: Official LIC PDFs downloaded into `data/raw_pdfs/` (`LIC_Jeevan Umang_Eng _141025.pdf`, `LIC_Bima Shree _Sales Brochure_Eng_06112025.pdf`, `LIC_Money Back 20 yrs Sales Brochure Eng_06112025.pdf`). Parsed into `data/parsed_markdown/`.
- **[Ticket 5: Terraform IaC Structure](issues/005-terraform-structure.md)**: Created modular Terraform architecture in `terraform/` (`provider.tf`, `variables.tf`, `gcs.tf`, `db.tf`, `cloud_run.tf`, `budget.tf`, `outputs.tf`).
- **[Ticket 6: Markdown Header & Table-Aware Semantic Chunker](issues/006-chunking-strategy.md)**: Implemented `MarkdownSemanticChunker` in `src/chunking/chunker.py`. Preserves header hierarchy context (`header_path`), keeps markdown tables unbroken, bounds chunks to 500-1000 tokens with overlap, and generates structured JSON chunks in `data/chunks/parsed_chunks.json`. Verified with test suite `tests/test_chunker.py`.
- **[Ticket 7: Vector Store & Embeddings Pipeline Setup](issues/007-vector-store-setup.md)**: Implemented `PolicyEmbedder` (`src/embeddings/embedder.py`) supporting Vertex AI (`text-embedding-004`) + deterministic offline feature fallback, and `VectorStore` (`src/vectorstore/store.py`) supporting cosine similarity search, metadata filtering, and local disk persistence. Ingested 71 chunks into `data/vector_store/`. Verified with unit tests `tests/test_vectorstore.py` and evaluation script `scripts/test_retrieval.py`.
- **[Ticket 8: RAG Retrieval & Gemini Function Calling Router](issues/008-rag-agent-router.md)**: Implemented production math payout calculator (`src/tools/math_tool.py`) and agent query router (`src/router/agent_router.py`). Supports `CALCULATION` (deterministic tool execution), `COMPARISON` (multi-doc vector synthesis), `POLICY_INQUIRY` (RAG retrieval with collapsible citations), and `OUT_OF_SCOPE` (grounding refusal guardrail). Verified with unit tests `tests/test_router.py`.
- **[Ticket 8B: Parent-Child Chunking & BM25 Hybrid Retrieval](issues/008b-hybrid-retrieval-parent-child.md)**: Added `parent_chunk_id` and metadata linkage to `MarkdownSemanticChunker`. Upgraded `VectorStore` (`src/vectorstore/store.py`) with BM25 Sparse Keyword Search and Reciprocal Rank Fusion (RRF) hybrid retrieval. Verified with unit tests `tests/test_hybrid_retrieval.py`.
- **[Ticket 9: FastAPI Backend REST Server](issues/009-fastapi-backend.md)**: Implemented production REST API server (`app/main.py`) exposing `/health`, `POST /api/v1/query` (Agentic RAG Router), `POST /api/v1/calculate` (Deterministic Payout Engine), and `GET /api/v1/policies`. Verified with unit tests `tests/test_fastapi.py`.
- **[Ticket 10: Streamlit Frontend UI](issues/010-streamlit-ui.md)**: Implemented interactive Streamlit UI (`app/ui.py`) with multi-turn chatbot, collapsible source citations, sidebar payout calculator with metric cards, and policy comparison matrix. Verified with syntax compilation test `tests/test_ui.py`.
- **[Ticket 11: Docker Containerization & Cloud Run Deployment Setup](issues/011-docker-deployment.md)**: Authored production multi-stage `Dockerfile` and `requirements.txt` locking dependencies for Cloud Run serverless container deployment.

## Open Tickets (Frontier)

- *All planned core system tickets (Tickets 1 to 11) completed! Ready for cloud deployment command execution.*

## Not yet specified
- **Frontend Framework:** Streamlit vs Next.js vs FastAPI + React for UI.
- **Data Ingestion Webhook:** Eventarc / Cloud Tasks configuration for automated PDF processing on upload.

## Out of scope

- Direct policy purchasing and payment gateways.
- Live agent handoff.
- User authentication and persistent cross-session profile storage.
