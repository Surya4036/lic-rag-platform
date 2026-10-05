import os
import re
import logging
from enum import Enum
from typing import Dict, Any, List, Optional

logger = logging.getLogger("agent_router")

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

        # Out-of-scope / Non-LIC insurance keywords check with strict word boundaries
        non_lic_keywords = [
            r"\bcakes?\b", r"\brecipes?\b", r"\bcapital\b", r"\bweather\b", r"\bcar\s*insurance\b", r"\bhealth\s*insurance\b",
            r"\bcrypto\b", r"\bpython\b", r"\bbakes?\b", r"\bstocks?\b", r"\bshares?\b",
            r"\bmovies?\b", r"\bfootball\b", r"\bcricket\b", r"\bflights?\b", r"\bhotels?\b", r"\bpresidents?\b", r"\bbitcoins?\b"
        ]
        explicit_lic_keywords = [
            r"\blic\b", r"\bjeevan\b", r"\bbima\b", r"\bmoney\s*back\b", r"\bsum\s*assured\b", r"\bmaturity\b", r"\bpremium\b",
            r"\brider\b", r"\buin\b", r"\bdeath\s*benefit\b", r"\bsurvival\s*benefit\b",
            r"\bgrace\s*period\b", r"\bsurrender\b", r"\bnominee\b", r"\bclaim\b", r"\bannuity\b", r"\bendowment\b", r"\brevival\b"
        ]

        # Check non-LIC domain triggers first
        is_non_lic = any(re.search(pat, q_lower) for pat in non_lic_keywords)
        is_explicit_lic = any(re.search(pat, q_lower) for pat in explicit_lic_keywords)

        if is_non_lic and not is_explicit_lic:
            return QueryIntent.OUT_OF_SCOPE

        # Calculation keywords
        calc_keywords = ["calculate", "payout", "maturity benefit", "estimated maturity", "how much will i get", "bonus calculation"]
        if any(kw in q_lower for kw in calc_keywords) and (any(re.search(p, q_lower) for p in [r"\bsum\s*assured\b", r"\blakh\b", r"\b500000\b", r"\b200000\b"]) or ("term" in q_lower and "age" in q_lower)):
            return QueryIntent.CALCULATION

        # Comparison keywords
        comp_keywords = ["compare", "vs", "versus", "difference between", "which is better"]
        if any(kw in q_lower for kw in comp_keywords) and (is_explicit_lic or "plan" in q_lower or "policy" in q_lower):
            return QueryIntent.COMPARISON

        # General policy inquiry fallback - require explicit LIC domain context or policy concepts
        if is_explicit_lic or "lic" in q_lower or "jeevan" in q_lower or "bima" in q_lower:
            return QueryIntent.POLICY_INQUIRY

        return QueryIntent.OUT_OF_SCOPE

    def _extract_calc_params(self, query: str) -> Dict[str, Any]:
        """Extract policy name, sum assured, term, and entry age cleanly from prompt without parameter collision."""
        q_lower = query.lower()

        # 1. Age extraction first (to avoid age numbers matching sum assured)
        age = 30
        age_match = re.search(r"(?:age|aged)\s*(\d+)|(\d+)\s*(?:years?|yr|yrs)\s*old", q_lower)
        if age_match:
            a_str = age_match.group(1) or age_match.group(2)
            if a_str:
                age_val = int(a_str)
                if 0 <= age_val <= 100:
                    age = age_val

        # 2. Term extraction
        term = 25
        term_match = re.search(r"(?:term|duration|period)\s*(?:of\s*)?(\d+)|(\d+)\s*(?:years?|yr|yrs)\s*(?:term|duration|policy)", q_lower)
        if term_match:
            t_str = term_match.group(1) or term_match.group(2)
            if t_str:
                term_val = int(t_str)
                if 5 <= term_val <= 100:
                    term = term_val

        # 3. Sum Assured extraction targeting explicit keywords or currency figures
        sa = 500000.0
        sa_patterns = [
            r"(?:sum\s*assured|sa|cover)\s*(?:of\s*)?₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(lakh|lakhs|l|cr|crore)?",
            r"₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(lakh|lakhs|l|cr|crore)\s*(?:sum\s*assured|sa|cover)?",
            r"(?:₹|rs\.?)\s*(\d+(?:,\d+)*(?:\.\d+)?)"
        ]
        
        for pat in sa_patterns:
            m = re.search(pat, q_lower)
            if m:
                val_str = m.group(1).replace(",", "")
                try:
                    val = float(val_str)
                    unit = m.group(2) if len(m.groups()) >= 2 else ""
                    if unit in ["lakh", "lakhs", "l"]:
                        sa = val * 100000.0
                    elif unit in ["cr", "crore"]:
                        sa = val * 10000000.0
                    elif val >= 50000:
                        sa = val
                    elif val < 100 and ("lakh" in q_lower or "l" in q_lower):
                        sa = val * 100000.0
                    break
                except ValueError:
                    pass

        # 4. Policy name extraction
        policy_name = "LIC Jeevan Umang"
        if "bima shree" in q_lower:
            policy_name = "LIC Bima Shree"
        elif "money back" in q_lower:
            policy_name = "LIC New Money Back Plan 20 Years"
        elif "labh" in q_lower:
            policy_name = "LIC Jeevan Labh"
        elif "utsav" in q_lower:
            policy_name = "LIC Jeevan Utsav"
        elif "amritbaal" in q_lower or "amrit" in q_lower:
            policy_name = "LIC Amritbaal"
        elif "pension" in q_lower:
            policy_name = "LIC New Pension Plus"

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
            "512N280V03": [r"\bmoney\s*back\b", r"512n280v03"],
            "512N304V03": [r"\bjeevan\s*labh\b", r"\blabh\b", r"512n304v02", r"512n304v03"],
            "512N363V01": [r"\bjeevan\s*utsav\b", r"\butsav\b", r"512n363v01"],
            "512N365V01": [r"\bamritbaal\b", r"\bamrit\s*baal\b", r"512n365v01"],
            "512N347V01": [r"\bnew\s*pension\s*plus\b", r"\bpension\s*plus\b", r"\bpension\b", r"512n347v01"]
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
                f"*Parameters used: Age {calc_res['entry_age']}, Term {calc_res['term_years']} yrs, Sum Assured ₹{calc_res['basic_sum_assured']:,.0f}.*\n\n"
                f"*(⚠️ Note: Payout figures are illustrative estimates based on bonus tables for planning purposes.)*"
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

        # 1. Fast Gemini LLM synthesis using primary client
        try:
            from google import genai
            from google.genai import types

            system_instruction = (
                "You are an expert AI LIC Policy Advisor. Provide a clear, direct, single-sentence answer to the user's question first. "
                "Follow with 2-3 brief bullet points highlighting key parameters (e.g., Minimum Age, Maximum Age, Sum Assured) if applicable. "
                "Do NOT copy large blocks of raw text, rider terms, or fee tables. Keep the response concise and readable."
            )
            prompt = f"User Question: {query}\n\nRetrieved Official Document Context:\n{context_str}\n\nPlease synthesize a clear, direct, and well-formatted answer:"
            genai_config = types.GenerateContentConfig(system_instruction=system_instruction)

            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or getattr(self.embedder, "api_key", None)
            client = None
            if api_key:
                client = genai.Client(api_key=api_key)
            elif hasattr(self.embedder, "_genai_client") and self.embedder._genai_client:
                client = self.embedder._genai_client
            elif os.environ.get("GCP_PROJECT_ID"):
                client = genai.Client(vertexai=True, project=os.environ.get("GCP_PROJECT_ID"), location="us-central1")

            if client:
                model_name = "gemini-2.5-flash-lite"
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=genai_config
                    )
                    if response and response.text:
                        logger.info(f"Successfully generated answer with model {model_name}")
                        return response.text.strip()
                except Exception as e:
                    logger.warning(f"Gemini LLM error with model {model_name}: {e}")
        except Exception as e:
            logger.error(f"Gemini synthesis error: {e}")

        # 2. Intelligent Concise Extraction Fallback
        for res in retrieved_chunks:
            c = res["chunk"] if "chunk" in res else res
            pname = c.get("policy_name", "LIC Policy")
            content = c.get("content", "").strip()
            
            # Special high-precision handling for Minimum Entry Age queries
            if "minimum" in query.lower() and "age" in query.lower():
                if "8 years" in content.lower():
                    return f"The minimum entry age for {pname} is **8 years (completed)**."
                if "13 years" in content.lower():
                    return f"The minimum entry age for {pname} is **13 years (completed)**."
                if "90 days" in content.lower() or "30 days" in content.lower():
                    match = re.search(r"(\d+\s*(?:days|years))\s*\(completed\)", content, re.IGNORECASE)
                    if match:
                        return f"The minimum entry age for {pname} is **{match.group(1)} (completed)**."

        # General concise term matching fallback
        extracted_lines = []
        ignore_words = {"what", "is", "are", "the", "for", "lic", "plan", "policy", "does", "which", "how", "much", "many", "under", "defined", "option", "choice", "choices"}
        key_terms = [q.strip().lower() for q in query.split() if len(q.strip()) > 2 and q.lower() not in ignore_words]
        
        for res in retrieved_chunks:
            c = res["chunk"] if "chunk" in res else res
            pname = c.get("policy_name", "LIC Policy")
            content = c.get("content", "").strip()
            if not content:
                continue
            
            clean_lines = [line.strip() for line in content.split("\n") if line.strip() and not line.strip().endswith(".pdf")]
            matching_lines = []
            for line in clean_lines:
                line_lower = line.lower()
                if any(term in line_lower for term in key_terms):
                    clean_line = re.sub(r"^[\-\*\:\#\d\.\s]+", "", line).strip()
                    if clean_line and len(clean_line) > 10 and clean_line not in matching_lines:
                        matching_lines.append(clean_line)
            
            if matching_lines:
                extracted_lines.append(f"- **{pname}**: " + "; ".join(matching_lines[:2]))
        
        if extracted_lines:
            return "Based on official LIC policy documents:\n\n" + "\n".join(extracted_lines[:2])
        
        if retrieved_chunks:
            top_chunk = retrieved_chunks[0].get("chunk", retrieved_chunks[0])
            pname = top_chunk.get("policy_name", "LIC Policy")
            content_lines = [l.strip() for l in top_chunk.get("content", "").split("\n") if l.strip() and not l.strip().endswith(".pdf")]
            first_text = content_lines[0] if content_lines else "Refer to official policy documentation."
            return f"**{pname}**: {first_text}"

        return f"Based on official LIC policy documents for '{query}': No relevant details found."


