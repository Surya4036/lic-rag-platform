## Question

What is the standardized naming convention for our GCP resources, and which GCP Region should we deploy to for lowest latency (given the target audience is India) and best feature availability (Gemini 1.5 Pro/Flash and Vector Search)?

*Label: wayfinder:task (HITL)*

---

## Resolution

- **Region**: `asia-south1` (Mumbai) will be used for all resources to ensure low latency. If Gemini 1.5 Pro is strictly needed and unavailable locally, we will route only that specific API call to a supported region (like `us-central1`).
- **Naming Convention**: `<project>-<resource>-<environment>`
  - Project prefix: `lic-rag`
  - Environment: `prod`
  - Examples: `lic-rag-api-prod`, `lic-rag-db-prod`, `lic-rag-docs-prod`, `lic_rag_vector_index_prod` (Vertex AI prefers underscores).

*Status: Closed*
