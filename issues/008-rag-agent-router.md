## Goal

Implement the **RAG Retrieval & Gemini Function Calling Router** (`src/router/agent_router.py`) that handles intent-based query routing (Calculation, Comparison, Policy Inquiry, Out-of-Scope Guardrail Refusal), invokes deterministic Python tools for math calculations, performs multi-document vector retrieval, and formats answers with strict source citations.

## Requirements

1. **Math Tool (`src/tools/math_tool.py`)**:
   - Implement deterministic LIC maturity benefit calculator function `calculate_maturity_benefit(policy_name, age, term, sum_assured)`.

2. **Agent Router (`src/router/agent_router.py`)**:
   - **Intent Classifier**: Categorize query into `CALCULATION`, `COMPARISON`, `POLICY_INQUIRY`, or `OUT_OF_SCOPE`.
   - **CALCULATION**: Extract parameters (`policy_name`, `age`, `term`, `sum_assured`) and invoke `calculate_maturity_benefit`.
   - **COMPARISON**: Retrieve relevant policy chunks for each policy mentioned, synthesize side-by-side comparison matrix with citations.
   - **POLICY_INQUIRY**: Perform vector search in `VectorStore`, formulate answer strictly grounded in retrieved chunks, attached with markdown citations (`[Doc Name > Header Path]`).
   - **OUT_OF_SCOPE Guardrail**: Refuse non-LIC / ungrounded queries with polite notice.

3. **Tests (`tests/test_router.py`)**:
   - Test intent classification accuracy.
   - Test math calculation routing.
   - Test comparison retrieval.
   - Test out-of-scope refusal guardrail.
