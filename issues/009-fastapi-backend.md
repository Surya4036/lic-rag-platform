## Goal

Implement the **FastAPI Backend REST Server** (`app/main.py`) exposing production REST API endpoints for query routing, payout calculations, policy chunk retrieval, and system health checks.

## Requirements

1. **Endpoints**:
   - `GET /`: Root welcome & API info.
   - `GET /health`: Health check endpoint.
   - `POST /api/v1/query`: Accepts user query payload (`{"query": str}`) and returns routed response with intent, answer text, citations, and tool execution status.
   - `POST /api/v1/calculate`: Direct endpoint for maturity benefit payout calculations (`{"policy_name": str, "sum_assured": float, "term": int, "age": int}`).
   - `GET /api/v1/policies`: List available policy plans in index.

2. **Tests (`tests/test_fastapi.py`)**:
   - Test all FastAPI endpoints using `fastapi.testclient.TestClient`.
