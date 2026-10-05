import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.math_tool import calculate_maturity_benefit
from src.router.agent_router import LICPolicyAgentRouter, QueryIntent

def test_math_tool_calculation():
    result = calculate_maturity_benefit(
        policy_name="LIC Jeevan Umang",
        sum_assured=500000,
        term=25,
        age=30
    )
    
    assert "error" not in result
    assert result["basic_sum_assured"] == 500000
    assert result["total_estimated_maturity_benefit"] > 500000
    assert "breakdown" in result

def test_intent_classification():
    router = LICPolicyAgentRouter()
    
    intent_calc = router.classify_intent("Calculate maturity benefit for 500000 sum assured in Jeevan Umang for 25 years age 30")
    assert intent_calc == QueryIntent.CALCULATION
    
    intent_comp = router.classify_intent("Compare LIC Jeevan Umang vs LIC Bima Shree")
    assert intent_comp == QueryIntent.COMPARISON
    
    intent_inq = router.classify_intent("What is the minimum entry age for LIC Bima Shree?")
    assert intent_inq == QueryIntent.POLICY_INQUIRY
    
    intent_out = router.classify_intent("How do I bake a chocolate cake?")
    assert intent_out == QueryIntent.OUT_OF_SCOPE

def test_router_execution_calculation():
    router = LICPolicyAgentRouter()
    response = router.process_query("Calculate payout for Jeevan Umang age 30 term 25 sum assured 500000")
    
    assert response["intent"] == QueryIntent.CALCULATION.value
    assert "500" in response["answer"] or "Maturity" in response["answer"]
    assert response["tool_call_used"] is True

def test_router_execution_policy_inquiry():
    router = LICPolicyAgentRouter()
    response = router.process_query("What is the minimum entry age for LIC Bima Shree?")
    
    assert response["intent"] == QueryIntent.POLICY_INQUIRY.value
    assert len(response["citations"]) > 0
    assert "Bima Shree" in response["answer"]

def test_router_execution_out_of_scope():
    router = LICPolicyAgentRouter()
    response = router.process_query("What is the capital of France?")
    
    assert response["intent"] == QueryIntent.OUT_OF_SCOPE.value
    assert "LIC" in response["answer"]
    assert "refuse" in response["answer"].lower() or "only answer" in response["answer"].lower() or "insurance" in response["answer"].lower()

def test_router_execution_stock_price_out_of_scope():
    router = LICPolicyAgentRouter()
    response = router.process_query("Can you tell me the stock price of Apple?")
    
    assert response["intent"] == QueryIntent.OUT_OF_SCOPE.value
    assert "LIC" in response["answer"] or "insurance" in response["answer"]

def test_comparison_targeted_retrieval():
    router = LICPolicyAgentRouter()
    query = "Compare LIC Jeevan Umang and LIC Bima Shree in terms of survival benefits and policy terms"
    response = router.process_query(query)
    
    assert response["intent"] == QueryIntent.COMPARISON.value
    citation_names = [c["policy_name"] for c in response["citations"]]
    
    # Verify ONLY Jeevan Umang and Bima Shree are retrieved, and Money Back Plan is excluded
    assert any("Jeevan Umang" in name for name in citation_names)
    assert any("Bima Shree" in name for name in citation_names)
    assert not any("Money Back" in name for name in citation_names)

