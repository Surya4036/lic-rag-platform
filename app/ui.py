import os
import sys
import requests
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.router.agent_router import LICPolicyAgentRouter
from src.tools.math_tool import calculate_maturity_benefit

API_URL = os.environ.get("FASTAPI_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="LIC Policy Advisor Platform",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ LIC Policy Advisor & Comparison Platform")
st.caption("Enterprise-Grade Agentic RAG Engine for LIC Insurance Policies")

# Initialize Local Fallback Router if API is not reachable
def get_local_router():
    return LICPolicyAgentRouter()

local_router = get_local_router()

def query_backend(prompt: str) -> dict:
    """Send query to FastAPI backend server with local fallback."""
    try:
        res = requests.post(f"{API_URL}/api/v1/query", json={"query": prompt}, timeout=30)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print("FastAPI query error:", e)
    # Fallback to direct python execution
    return local_router.process_query(prompt)

def calculate_backend(policy_name: str, sum_assured: float, term: int, age: int) -> dict:
    """Send payout calculation to FastAPI backend with local fallback."""
    try:
        payload = {
            "policy_name": policy_name,
            "sum_assured": sum_assured,
            "term": term,
            "age": age
        }
        res = requests.post(f"{API_URL}/api/v1/calculate", json=payload, timeout=30)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print("FastAPI calculate error:", e)
    return calculate_maturity_benefit(policy_name=policy_name, sum_assured=sum_assured, term=term, age=age)

# Sidebar - Math Payout Calculator Tool
st.sidebar.header("🧮 Maturity Benefit Calculator")
st.sidebar.markdown("Deterministic Python Math Engine")

calc_plan = st.sidebar.selectbox(
    "Select Plan",
    ["LIC Jeevan Umang", "LIC Bima Shree", "LIC New Money Back Plan 20 Years"]
)
calc_sa = st.sidebar.number_input("Sum Assured (₹)", min_value=100000, max_value=10000000, value=500000, step=50000)
calc_term = st.sidebar.slider("Policy Term (Years)", min_value=10, max_value=35, value=25)
calc_age = st.sidebar.slider("Entry Age (Years)", min_value=18, max_value=65, value=30)

if st.sidebar.button("Calculate Payout"):
    calc_res = calculate_backend(calc_plan, float(calc_sa), calc_term, calc_age)
    b = calc_res["breakdown"]
    
    st.sidebar.subheader("Payout Breakdown")
    st.sidebar.metric("Basic Sum Assured", f"₹{b['basic_sum_assured']:,.0f}")
    st.sidebar.metric("Vested Reversionary Bonus", f"₹{b['total_reversionary_bonus']:,.0f}")
    st.sidebar.metric("Final Additional Bonus (FAB)", f"₹{b['final_additional_bonus']:,.0f}")
    st.sidebar.metric("Total Estimated Maturity", f"₹{calc_res['total_estimated_maturity_benefit']:,.0f}")

# Main Tabs
tab1, tab2 = st.tabs(["💬 AI Advisor Chat", "📊 Policy Catalog & Comparison"])

with tab1:
    st.subheader("LIC Policy Assistant (Agentic RAG)")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I am your AI LIC Policy Advisor. Ask me anything about LIC plans, entry ages, survival benefits, policy comparisons, or payout estimates.",
                "intent": "POLICY_INQUIRY",
                "citations": []
            }
        ]

    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                if msg.get("intent"):
                    st.caption(f"Intent: **{msg['intent']}**")
                st.markdown(msg["content"])
                if msg.get("citations"):
                    with st.expander("📚 Source Attribution & Citations"):
                        for cit in msg["citations"]:
                            st.markdown(f"- **{cit.get('policy_name', 'Source')}** ({cit.get('policy_uin', '')}) > *{cit.get('header_path', '')}*")

    if user_prompt := st.chat_input("Ask a question about LIC policies..."):
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing policy documents and calculating payouts..."):
                    response_data = query_backend(user_prompt)
                    
                    intent = response_data.get("intent", "POLICY_INQUIRY")
                    answer = response_data.get("answer", "")
                    citations = response_data.get("citations", [])

                    if intent:
                        st.caption(f"Intent: **{intent}**")
                    st.markdown(answer)
                    if citations:
                        with st.expander("📚 Source Attribution & Citations"):
                            for cit in citations:
                                st.markdown(f"- **{cit.get('policy_name', 'Source')}** ({cit.get('policy_uin', '')}) > *{cit.get('header_path', '')}*")

        st.session_state.messages.append({"role": "user", "content": user_prompt})
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "intent": intent,
            "citations": citations
        })

        st.rerun()

with tab2:
    st.subheader("LIC Policy Matrix Comparison")
    st.markdown("""
    | Feature / Parameter | **LIC Jeevan Umang** (512N312V03) | **LIC Bima Shree** (512N316V03) | **LIC Money Back 20 Yrs** (512N280V03) |
    |---|---|---|---|
    | **Plan Type** | Whole Life (Par, Savings) | High Networth Individual (Par) | Money Back (Par, Savings) |
    | **Min Basic Sum Assured** | ₹2,00,000 | ₹10,00,000 | ₹2,00,000 |
    | **Policy Term** | 100 - Age at Entry | 14, 16, 18, 20, 24, 28 Yrs | 20 Years |
    | **Survival Benefits** | 8% BSA annually post-PPT | 30% to 45% of BSA in intervals | 20% of BSA at 5th, 10th, 15th yr |
    | **Maturity Benefit** | Sum Assured + Bonuses | Sum Assured + Guaranteed Additions | 40% BSA + Bonuses |
    """)
