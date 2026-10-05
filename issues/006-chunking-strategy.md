## Goal

Implement a **Markdown Header & Table-Aware Semantic Chunker** that takes the parsed GFM Markdown files from `data/parsed_markdown/` and splits them into clean contextual chunks ready for vector embeddings.

## Requirements

1. **Header Context Inheritance**: Each chunk must carry its parent section headings (e.g. `[LIC Jeevan Umang > Eligibility Conditions]`) as metadata/context prefix so the LLM understands the exact section context.
2. **Unbroken Table Preservation**: Markdown tables (`| header | header |`) must never be split across chunk boundaries.
3. **Chunk Size & Overlap**: Target chunk size ~500-1000 tokens with 100 token overlap for narrative prose.
4. **Metadata Payload**: Output JSON structure per chunk:
   ```json
   {
     "chunk_id": "jeevan-umang-sec-3-chunk-1",
     "policy_uin": "512N312V03",
     "policy_name": "LIC Jeevan Umang",
     "header_path": "LIC Jeevan Umang > Eligibility Conditions",
     "content": "...",
     "contains_table": true
   }
   ```
