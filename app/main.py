import os
import sys
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.router.agent_router import LICPolicyAgentRouter
from src.tools.math_tool import calculate_maturity_benefit

app = FastAPI(
    title="LIC Policy Advisor & Comparison Platform API",
    description="Agentic RAG Engine for LIC Policy Inquiries, Comparisons, and Deterministic Payout Calculations",
    version="1.0.0"
)

router = LICPolicyAgentRouter()

class QueryRequest(BaseModel):
    query: str = Field(..., json_schema_extra={"example": "What is the minimum entry age for LIC Bima Shree?"})

class CalculateRequest(BaseModel):
    policy_name: str = Field("LIC Jeevan Umang", json_schema_extra={"example": "LIC Jeevan Umang"})
    sum_assured: float = Field(500000.0, json_schema_extra={"example": 500000.0})
    term: int = Field(25, json_schema_extra={"example": 25})
    age: int = Field(30, json_schema_extra={"example": 30})

@app.get("/")
def read_root():
    return {
        "message": "Welcome to LIC Policy Advisor & Comparison Platform API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "lic-policy-advisor-api"
    }

@app.post("/api/v1/query")
def process_query_endpoint(request: QueryRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return router.process_query(request.query)

@app.post("/api/v1/calculate")
def calculate_endpoint(request: CalculateRequest):
    return calculate_maturity_benefit(
        policy_name=request.policy_name,
        sum_assured=request.sum_assured,
        term=request.term,
        age=request.age
    )

@app.get("/api/v1/policies")
def list_policies():
    unique_policies = {}
    for chunk in router.vector_store.chunks:
        uin = chunk.get("policy_uin", "N/A")
        name = chunk.get("policy_name", "N/A")
        if uin not in unique_policies:
            unique_policies[uin] = {
                "policy_name": name,
                "policy_uin": uin
            }
    return {
        "policies": list(unique_policies.values())
    }
