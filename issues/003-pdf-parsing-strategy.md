## Decision: PDF Parsing Strategy

**Selected Strategy**: `pymupdf4llm` (PyMuPDF Layout-Aware Markdown Extraction).

### Benchmark & Findings on LIC Sales Brochures
- **`pymupdf4llm`**: Converts complex nested PDF tables (e.g. eligibility tables, survival benefit payout schedules, minimum instalment matrices) into valid GFM Markdown tables.
- **Layout Preservation**: Retains header structures, line breaks (`<br>`), bulleted lists, and section hierarchy without scrambling multi-column data.
- **Performance**: High performance local Python execution (~0.5s per PDF document), requiring zero external paid API calls (e.g. Document AI / LlamaParse), perfectly preserving our GCP budget.

### Ingestion Flow
1. PDF uploaded / placed in `data/raw_pdfs/`.
2. Parsed via `pymupdf4llm.to_markdown(pdf_path)`.
3. Processed into section chunks preserving table integrity for vector indexing & Gemini RAG.
