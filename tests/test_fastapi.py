import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "lic-policy-advisor-api"}

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_query_endpoint_calculation():
    payload = {"query": "Calculate payout for Jeevan Umang age 30 term 25 sum assured 500000"}
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "CALCULATION"
    assert "500" in data["answer"] or "Maturity" in data["answer"]
    assert data["tool_call_used"] is True

def test_query_endpoint_inquiry():
    payload = {"query": "What is the minimum entry age for LIC Bima Shree?"}
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "POLICY_INQUIRY"
    assert len(data["citations"]) > 0

def test_calculate_endpoint():
    payload = {
        "policy_name": "LIC Jeevan Umang",
        "sum_assured": 500000.0,
        "term": 25,
        "age": 30
    }
    response = client.post("/api/v1/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["basic_sum_assured"] == 500000.0
    assert data["total_estimated_maturity_benefit"] > 500000.0

def test_policies_endpoint():
    response = client.get("/api/v1/policies")
    assert response.status_code == 200
    data = response.json()
    assert "policies" in data
    assert len(data["policies"]) > 0
