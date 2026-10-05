## Question

Before we build the full cloud infrastructure, we need to prove that an LLM can accurately calculate the LIC Maturity Benefit (Basic Sum Assured + Vested Simple Reversionary Bonuses + Final Additional Bonus) via a Python tool.

Can we build a quick local script to test the math formula against a known LIC policy example to ensure this approach is viable?

*Label: wayfinder:prototype (HITL)*

---

## Resolution

- Built a local prototype (`prototypes/math_tool.py`) proving the math tool abstraction.
- The prototype successfully demonstrates taking LLM-extracted parameters (plan, SA, term, age) and calculating the deterministic maturity benefit using hardcoded logic.
- We confirmed the math boundaries: (Basic Sum Assured) + ((SA/1000) * Bonus Rate * Term) + ((SA/1000) * FAB Rate).
- **Conclusion:** This approach is fully viable. The agent will route to this logic instead of hallucinating math. 

*Status: Closed*
