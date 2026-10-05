## Goal

Implement an interactive **Streamlit Frontend UI** (`app/ui.py`) for the LIC Policy Advisor & Comparison Platform. The UI connects directly to our FastAPI backend API, featuring an AI chat interface with source citations, a dedicated maturity benefit payout calculator sidebar, and a policy comparison dashboard.

## Requirements

1. **AI Policy Advisor Chat Tab (`st.chat_input`)**:
   - Interactive multi-turn chat experience connected to `POST /api/v1/query`.
   - Displays query intent badge (`CALCULATION`, `COMPARISON`, `POLICY_INQUIRY`, `OUT_OF_SCOPE`).
   - Formats responses with collapsible source citations (`[Policy Name > Section Path]`).

2. **Interactive Payout Calculator Sidebar**:
   - User inputs for Policy Name (dropdown: Jeevan Umang, Bima Shree, Money Back 20 Yrs), Basic Sum Assured (slider/number input), Policy Term, and Entry Age.
   - Invokes `POST /api/v1/calculate` and renders metric cards (`st.metric`) for Sum Assured, Vested Bonus, FAB, and Total Estimated Maturity Benefit.

3. **Policy Catalog & Plan Comparison View**:
   - Fetches available plans from `GET /api/v1/policies`.
   - Side-by-side comparative feature matrix display.
