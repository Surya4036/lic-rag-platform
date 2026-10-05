import os
import re
from enum import Enum
from typing import Dict, Any, List, Optional

from src.embeddings.embedder import PolicyEmbedder
from src.vectorstore.store import VectorStore
from src.tools.math_tool import calculate_maturity_benefit

class QueryIntent(Enum):
    CALCULATION = "CALCULATION"
    COMPARISON = "COMPARISON"
    POLICY_INQUIRY = "POLICY_INQUIRY"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"

class LICPolicyAgentRouter:
    """
    Agentic RAG Router for LIC Policy Advisor platform.
    Routes user queries to Math Execution Tool, Policy Vector Search,
    Multi-Document Comparison, or Grounding Refusal Guardrail.
    """
    def __init__(self, vector_store_dir: Optional[str] = None):
        self.embedder = PolicyEmbedder()
        self.vector_store = VectorStore()
        
        if vector_store_dir is None:
            vector_store_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "vector_store")
            
        if os.path.exists(vector_store_dir):
            self.vector_store.load(vector_store_dir)

    def classify_intent(self, query: str) -> QueryIntent:
        q_lower = query.lower()

        # Out-of-scope / Non-LIC insurance keywords check
        non_lic_keywords = [
            "cake", "recipe", "capital of", "weather", "car insurance", "health insurance",
            "crypto", "python code", "bake", "stock", "stock price", "apple", "shares",
            "movie", "football", "cricket", "flight", "hotel", "president", "bitcoin"
        ]
        lic_policy_keywords = [
            "lic", "jeevan", "bima", "money back", "sum assured", "maturity", "premium",
            "policy", "rider", "uin", "term", "insurance", "death benefit", "survival benefit",
            "grace period", "surrender", "loan", "nominee", "claim", "annuity", "endowment", "revival"
        ]

        if any(kw in q_lower for kw in non_lic_keywords) and not any(kw in q_lower for kw in lic_policy_keywords):
            return QueryIntent.OUT_OF_SCOPE

        # Calculation keywords
        calc_keywords = ["calculate", "payout", "maturity benefit", "estimated maturity", "how much will i get", "bonus calculation"]
        if any(kw in q_lower for kw in calc_keywords) and ("sum assured" in q_lower or "lakh" in q_lower or "500000" in q_lower or "200000" in q_lower or "term" in q_lower):
            return QueryIntent.CALCULATION

        # Comparison keywords
        comp_keywords = ["compare", "vs", "versus", "difference between", "which is better"]
        if any(kw in q_lower for kw in comp_keywords) and (any(kw in q_lower for kw in lic_policy_keywords) or "plan" in q_lower or "policy" in q_lower):
            return QueryIntent.COMPARISON

        # General policy inquiry fallback - require LIC / insurance domain context or policy concepts
        if any(kw in q_lower for kw in lic_policy_keywords) or "plan" in q_lower or "benefit" in q_lower:
            return QueryIntent.POLICY_INQUIRY

        return QueryIntent.OUT_OF_SCOPE

    def _extract_calc_params(self, query: str) -> Dict[str, Any]:
        """Extract policy name, sum assured, term, and entry age from user prompt."""
        # Sum Assured extraction
        sa_match = re.search(r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakh|l)?", query, re.IGNORECASE)
        sa = 500000.0
        if sa_match:
            val_str = sa_match.group(1).replace(",", "")
            val = float(val_str)
            if "lakh" in query.lower() or "l" in sa_match.group(0).lower() and val < 100:
                sa = val * 100000.0
            elif val >= 50000:
                sa = val

        # Term extraction
        term_match = re.search(r"(\d+)\s*(?:years?|yr|term)", query, re.IGNORECASE)
        term = int(term_match.group(1)) if term_match else 25

        # Age extraction
        age_match = re.search(r"age\s*(\d+)|(\d+)\s*years?\s*old", query, re.IGNORECASE)
        age = 30
        if age_match:
            age_str = age_match.group(1) or age_match.group(2)
            age = int(age_str)

        # Policy name extraction
        policy_name = "LIC Jeevan Umang"
        if "bima shree" in query.lower():
            policy_name = "LIC Bima Shree"
        elif "money back" in query.lower():
            policy_name = "LIC New Money Back Plan 20 Years"

        return {
            "policy_name": policy_name,
            "sum_assured": sa,
            "term": term,
            "age": age
        }

    def _detect_mentioned_policy_uins(self, query: str) -> List[str]:
        """Detect which LIC policy UINs are explicitly mentioned in the user query."""
        q_lower = query.lower()
        mentioned = []
        
        policy_patterns = {
            "512N312V03": [r"\bjeevan\s*umang\b", r"\bumang\b", r"512n312v03", r"\b745\b"],
            "512N316V03": [r"\bbima\s*shree\b", r"\bbima\s*sri\b", r"\bshree\b", r"512n316v03"],
            "512N280V03": [r"\bmoney\s*back\b", r"512n280v03"]
        }
        
        for uin, patterns in policy_patterns.items():
            for pat in patterns:
                if re.search(pat, q_lower):
                    if uin not in mentioned:
                        mentioned.append(uin)
                    break
        return mentioned

    def process_query(self, query: str) -> Dict[str, Any]:
        intent = self.classify_intent(query)

        if intent == QueryIntent.OUT_OF_SCOPE:
            return {
                "intent": intent.value,
                "answer": "I am an AI LIC Policy Advisor platform. I can only assist with official LIC insurance plans, policy details, maturity benefit calculations, and plan comparisons. Please ask an insurance policy related question.",
                "citations": [],
                "tool_call_used": False
            }

        if intent == QueryIntent.CALCULATION:
            params = self._extract_calc_params(query)
            calc_res = calculate_maturity_benefit(**params)
            
            b = calc_res["breakdown"]
            formatted_answer = (
                f"### Maturity Benefit Estimate for **{calc_res['policy_name']}**\n\n"
                f"- **Basic Sum Assured:** ₹{b['basic_sum_assured']:,.2f}\n"
                f"- **Vested Simple Reversionary Bonus:** ₹{b['total_reversionary_bonus']:,.2f}\n"
                f"- **Final Additional Bonus (FAB):** ₹{b['final_additional_bonus']:,.2f}\n\n"
                f"**Total Estimated Maturity Benefit:** **₹{calc_res['total_estimated_maturity_benefit']:,.2f}**\n\n"
                f"*Parameters used: Age {calc_res['entry_age']}, Term {calc_res['term_years']} yrs, Sum Assured ₹{calc_res['basic_sum_assured']:,.0f}."
            )
            return {
                "intent": intent.value,
                "answer": formatted_answer,
                "citations": [{"source": "LIC Math Execution Tool", "section": "Deterministic Bonus Tables"}],
                "tool_call_used": True
            }

        if intent == QueryIntent.COMPARISON:
            q_vec = self.embedder.embed_query(query)
            mentioned_uins = self._detect_mentioned_policy_uins(query)

            retrieved = []
            if mentioned_uins:
                per_policy_k = max(2, 4 // len(mentioned_uins))
                for uin in mentioned_uins:
                    policy_res = self.vector_store.hybrid_search(query, q_vec, top_k=per_policy_k, policy_uin_filter=uin)
                    retrieved.extend(policy_res)
            else:
                retrieved = self.vector_store.hybrid_search(query, q_vec, top_k=4)

            citations = []
            chunk_sections = []
            for res in retrieved:
                c = res["chunk"]
                citations.append({
                    "policy_name": c["policy_name"],
                    "policy_uin": c["policy_uin"],
                    "header_path": c["header_path"]
                })
                clean_content = c['content'].strip()
                chunk_sections.append(f"#### 📄 {c['policy_name']} ({c['policy_uin']})\n**Section:** *{c['header_path']}*\n\n{clean_content}")

            retrieved_text = "\n\n---\n\n".join(chunk_sections)

            synthesized = self._synthesize_answer(query, retrieved, intent)
            formatted_answer = (
                f"### Policy Comparison Summary\n\n"
                f"{synthesized}\n\n"
                f"*(Refer to the **Policy Catalog & Comparison** tab for full side-by-side matrix view)*"
            )
            return {
                "intent": intent.value,
                "answer": formatted_answer,
                "citations": citations,
                "tool_call_used": False
            }

        # POLICY_INQUIRY
        q_vec = self.embedder.embed_query(query)
        mentioned_uins = self._detect_mentioned_policy_uins(query)

        if mentioned_uins:
            retrieved = []
            per_policy_k = max(4, 5 // len(mentioned_uins))
            for uin in mentioned_uins:
                policy_res = self.vector_store.hybrid_search(query, q_vec, top_k=per_policy_k, policy_uin_filter=uin)
                retrieved.extend(policy_res)
        else:
            retrieved = self.vector_store.hybrid_search(query, q_vec, top_k=4)

        citations = []
        for res in retrieved:
            c = res["chunk"]
            citations.append({
                "policy_name": c["policy_name"],
                "policy_uin": c["policy_uin"],
                "header_path": c["header_path"]
            })

        synthesized_answer = self._synthesize_answer(query, retrieved, intent)

        return {
            "intent": intent.value,
            "answer": synthesized_answer,
            "citations": citations,
            "tool_call_used": False
        }

    def _format_clean_markdown(self, text: str) -> str:
        """Sanitizes PyMuPDF multi-line header artifacts and ensures blank line separation before/after markdown tables."""
        # Sanitize known PyMuPDF fragmented table headers (Jeevan Umang / Bima Shree premium tables)
        text = re.sub(
            r"\|\s*\*\*AGE\*\*\s*\|\s*<br>\s*\*\*15\*\*\s*\|\s*\*\*PREMIUM PA\*\*\s*<br>\s*\*\*20\*\*\s*\|\s*\*\*YING TERM\*\*\s*<br>\s*\*\*25\*\*\s*\|\s*<br>\s*\*\*30\*\*\s*\|",
            "| **Age** | **PPT 15 Yrs** | **PPT 20 Yrs** | **PPT 25 Yrs** | **PPT 30 Yrs** |",
            text,
            flags=re.IGNORECASE
        )
        text = re.sub(
            r"\|\s*\*\*AGE\*\*\s*\|\s*\*\*15\*\*\s*\|\s*\*\*PREMIUM PA\*\*\s*\*\*20\*\*\s*\|\s*\*\*YING TERM\*\*\s*\*\*25\*\*\s*\|\s*\*\*30\*\*\s*\|",
            "| **Age** | **PPT 15 Yrs** | **PPT 20 Yrs** | **PPT 25 Yrs** | **PPT 30 Yrs** |",
            text,
            flags=re.IGNORECASE
        )

        lines = text.split("\n")
        formatted = []
        in_table = False
        
        for line in lines:
            line_str = line.strip()
            if not line_str:
                if formatted and formatted[-1] != "":
                    formatted.append("")
                continue
                
            is_table_line = line_str.startswith("|")
            if is_table_line:
                if not in_table and formatted and formatted[-1] != "":
                    formatted.append("")
                in_table = True
                # Clean up <br> tags in header cells
                if "<br>" in line_str and ("PREMIUM" in line_str or "AGE" in line_str or "TERM" in line_str or "YING" in line_str):
                    line_str = re.sub(r"<br\s*/?>", " ", line_str, flags=re.IGNORECASE)
                    line_str = re.sub(r"\s+", " ", line_str)
            else:
                if in_table and formatted and formatted[-1] != "":
                    formatted.append("")
                in_table = False
                
            formatted.append(line_str)
            
        return "\n".join(formatted)

    def _synthesize_answer(self, query: str, retrieved_chunks: List[Dict[str, Any]], intent: QueryIntent) -> str:
        """
        Synthesizes a clean, direct, human-readable answer from retrieved chunks using Gemini LLM when API key is available,
        or an intelligent extraction fallback when offline.
        """
        context_blocks = []
        for i, res in enumerate(retrieved_chunks, 1):
            c = res["chunk"] if "chunk" in res else res
            pname = c.get("policy_name", "LIC Policy")
            hdr = c.get("header_path", "General")
            content = self._format_clean_markdown(c.get("content", "").strip())
            context_blocks.append(f"Document Chunk #{i} [{pname} - Section: {hdr}]:\n{content}")

        context_str = "\n\n---\n\n".join(context_blocks)

        # 1. Try Gemini LLM synthesis if client is available
        if hasattr(self.embedder, "_genai_client") and self.embedder._genai_client:
            try:
                system_instruction = (
                    "You are an expert AI LIC Policy Advisor. Answer the user's question directly, concisely, and accurately "
                    "using ONLY the provided official LIC policy context documents below. "
                    "Do NOT copy large blocks of raw text, rider terms, or fee tables unless directly requested. "
                    "Format key facts as clear bullet points or markdown tables. "
                    "If the answer is not contained in the context, state clearly that the provided policy documents do not specify this detail."
                )
                prompt = f"User Question: {query}\n\nRetrieved Official Document Context:\n{context_str}\n\nPlease synthesize a clear, direct, and well-formatted answer:"
                
                clients_to_try = [self.embedder._genai_client]
                if self.embedder.gcp_project:
                    try:
                        from google import genai
                        clients_to_try.append(genai.Client(vertexai=True, project=self.embedder.gcp_project, location="us-central1"))
                        clients_to_try.append(genai.Client(vertexai=True, project=self.embedder.gcp_project, location="global"))
                    except Exception:
                        pass

                for client in clients_to_try:
                    for model_name in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.0-flash-001", "gemini-1.5-pro"]:
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=prompt,
                                config={"system_instruction": system_instruction}
                            )
                            if response and response.text:
                                return response.text.strip()
                        except Exception:
                            continue
            except Exception:
                pass

        # 2. Intelligent Offline Fallback Extraction
        extracted_points = []
        for res in retrieved_chunks:
            c = res["chunk"] if "chunk" in res else res
            pname = c.get("policy_name", "LIC Policy")
            hdr = c.get("header_path", "General")
            content = c.get("content", "").strip()
            
            if not content:
                continue
                
            clean_section_text = self._format_clean_markdown(content)
            extracted_points.append(f"### **{pname}** (*{hdr}*)\n{clean_section_text}")
        
        if extracted_points:
            return "Based on official LIC policy documents, here are the relevant details:\n\n" + "\n\n---\n\n".join(extracted_points)
        
        return f"Based on official LIC policy documents for '{query}':\n\nNo relevant details found."


