# Product Requirements Document (PRD)

**Project Name:** LIC Policy Advisor & Comparison Platform (Agentic RAG Engine)
**Author:** AI Assistant (via write-a-prd skill)
**Date:** 2026-10-04
**Status:** Draft

---

## 1. Overview / Executive Summary

### Problem Statement
The Life Insurance Corporation of India (LIC) offers dozens of active insurance plans across Term, Endowment, Money-Back, Annuity/Pension, and ULIP categories. Policy brochures and sales circulars are dense PDFs packed with complex parameters: entry ages, Policy Terms (PT), Premium Paying Terms (PPT), Riders, Bonus Rates, Survival Benefits, and Surrender Values. Customers and buyers struggle to compare these policies or determine which plan best aligns with their demographic profile and financial goals.

### Proposed Solution
An **Enterprise-Grade AI Assistant and Multi-Modal RAG Platform** tailored for LIC policies. The system ingests official LIC PDF documents, parses complex tabular data and bonus calculations, and uses a multi-agent workflow to provide persona-based recommendations, side-by-side plan comparisons, and exact premium/payout calculations via a dedicated math tool, complete with verifiable source attribution.

---

## 2. Goals & Objectives

**Business Goals:**
* Simplify the discovery and comparison of LIC policies for end-users.
* Provide highly accurate, mathematically sound estimates for maturity benefits and premiums.

**Key Metrics for Success (KPIs):**
* **Query Latency:** RAG query responses delivered within $\le 2.5\text{ seconds}$.
* **Accuracy Rate:** >95% accuracy on exact math calculations for maturity benefits.
* **Hallucination Rate:** Near 0% due to strict grounding constraints (must refuse non-LIC or ungrounded queries).
* **Infrastructure Cost:** Maintain operating costs strictly within the specified ₹26,000 budget cap.

---

## 3. User Stories / Use Cases

* **As a Young Professional (25–35 yrs),** I want to ask "Should I pick LIC Digi Term or New Endowment Plan?" so that I can decide between low-cost pure term cover and long-term savings.
* **As a Parent / Family Planner,** I want to compare "Amritbaal vs Jeevan Labh" for a 3-year-old so that I can plan goal-based finances for their higher education.
* **As a Retiree / Senior Citizen,** I want to know the difference between "Jeevan Akshay VII and New Jeevan Shanti" so that I can secure guaranteed lifetime income and annuity options.

---

## 4. Functional Requirements

### 4.1 Data Ingestion & Indexing Pipeline
* **Multi-Format Extraction:** Parse LIC PDF brochures, extracting layout structures, nested tables (e.g., age vs. term premium matrices), and fine-print clauses.
* **Hierarchical Chunking:** Implement Parent-Child Document Chunking to preserve context.
  * **Child Chunks (~200–300 tokens):** Specific rules, age caps, rider options.
  * **Parent Chunks (~1000 tokens):** Entire policy summary sections.
* **Metadata Schema:** Must include `plan_name`, `plan_number`, `category`, `min_entry_age`, `max_entry_age`, `min_sum_assured`, `page_number`, and `doc_url`.

### 4.2 Agentic RAG Engine
* **Hybrid Search:** Combine Dense Vector Embeddings (Vertex AI Text Embeddings) with Sparse Keyword Search (PostgreSQL `pgvector` / BM25).
* **Intent-Based Routing:**
  * **Direct Query:** Simple lookup of policy features.
  * **Comparison Request:** Fetches data across multiple documents and structures a side-by-side comparison matrix.
  * **Calculation Query:** Routes numeric questions to an internal Python execution tool instead of relying on LLM math.
* **Source Attribution:** Every response must display collapsible citations with exact source PDF document name and page number.

### 4.3 Interactive Math Engine (Tool Calling)
* **Python Payout Calc Tool:** Execution for estimating total maturity benefits: `Basic Sum Assured + Vested Simple Reversionary Bonuses + Final Additional Bonus (FAB)`.

---

## 5. Non-Functional Requirements

* **Performance / Latency:** End-to-end response time $\le 2.5\text{ seconds}$.
* **Security & Guardrails:** System must refuse to answer non-LIC or ungrounded insurance queries using Strict Grounding checks.
* **Architecture / Deployment:** GCP Cloud Run (Containerized FastAPI, Scale to 0), Vertex AI Studio (Gemini 1.5 Pro/Flash, Text Embeddings), Vertex AI Vector Search, Cloud SQL (PostgreSQL 15 + pgvector), Cloud Storage, and Cloud Tasks.
* **Cost Constraints:** Cap credit usage with automated GCP budget alerts set at 25%, 50%, 75%, and 100% of ₹26,000. Auto-undeploy Vertex AI Vector Search index endpoints during idle developer periods.

---

## 6. Out of Scope

* **Direct Policy Purchasing:** The system will not process payments or directly issue policies. It is an advisory/comparison tool only.
* **Live Agent Handoff:** Integration with a human customer support center is not planned for v1.0.
* **User Authentication/Profiles:** v1.0 will not save user chat histories or profiles across sessions (unless specifically added to the UI scope later).

---

## 7. Dependencies & Assumptions

* **Dependencies:**
  * Availability and reliability of GCP services (Vertex AI, Cloud SQL).
  * Access to high-quality, readable LIC policy PDFs for the ingestion pipeline.
* **Assumptions:**
  * Formulae for calculating bonuses (like FAB and Reversionary Bonuses) can be accurately modeled in Python based on the PDF charts.
  * LLM context windows (Gemini 1.5) are large enough to handle multiple parent chunks during comparison queries.

---

## 8. Timeline / Milestones

* **Phase 1 (Week 1):** Setup & Terraform IaC (Provision GCP infra using Terraform, set up budget alerts).
* **Phase 2 (Week 2):** PDF Parsing & Ingestion (Scrape/clean 10–15 major LIC PDFs, build chunking, push embeddings).
* **Phase 3 (Week 3):** Agentic API & Tools (Implement FastAPI backend with LangGraph/LlamaIndex router + Python Payout Calculator tool).
* **Phase 4 (Week 4):** CI/CD & Deploy (Build UI via Streamlit/Next.js, configure GitHub Actions, author README.md).
