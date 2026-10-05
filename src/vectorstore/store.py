import os
import re
import math
import json
import numpy as np
from typing import List, Dict, Any, Optional

class VectorStore:
    """
    Hybrid Vector Store for LIC Policy Chunks with Dense Vector Similarity,
    BM25 Sparse Keyword Search, Reciprocal Rank Fusion (RRF), and Metadata Filtering.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.k1 = k1
        self.b = b
        self.doc_tokens: List[List[str]] = []
        self.doc_lens: List[int] = []
        self.avg_doc_len: float = 0.0
        self.df: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

    STOP_WORDS = {
        "what", "is", "the", "for", "in", "of", "and", "or", "a", "an", "to", "on", "each",
        "at", "by", "with", "from", "as", "be", "this", "that", "it", "are", "was", "were",
        "will", "shall", "can", "has", "have", "had", "which", "who", "whom", "whose", "where", "when", "how"
    }

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"\w+", text.lower())
        return [t for t in tokens if t not in self.STOP_WORDS and len(t) > 1]

    def _build_bm25_index(self):
        """Builds BM25 term frequency and IDF index across all stored chunks."""
        self.doc_tokens = [
            self._tokenize(f"{c.get('policy_name', '')} {c.get('header_path', '')} {c.get('content', '')}")
            for c in self.chunks
        ]
        self.doc_lens = [len(tokens) for tokens in self.doc_tokens]
        num_docs = len(self.chunks)
        self.avg_doc_len = sum(self.doc_lens) / num_docs if num_docs > 0 else 1.0

        # Calculate Document Frequency (DF)
        self.df = {}
        for tokens in self.doc_tokens:
            unique_terms = set(tokens)
            for t in unique_terms:
                self.df[t] = self.df.get(t, 0) + 1

        # Calculate IDF
        self.idf = {}
        for t, count in self.df.items():
            self.idf[t] = math.log(1.0 + (num_docs - count + 0.5) / (count + 0.5))

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Adds chunks and corresponding embedding vectors to vector store."""
        if not chunks or not embeddings:
            return

        emb_matrix = np.array(embeddings, dtype=np.float32)

        # Normalize matrix rows to unit L2 vectors
        norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        emb_matrix = emb_matrix / norms

        if self.embeddings is None or len(self.embeddings) == 0:
            self.embeddings = emb_matrix
            self.chunks = list(chunks)
        else:
            self.embeddings = np.vstack([self.embeddings, emb_matrix])
            self.chunks.extend(chunks)

        self._build_bm25_index()

    def bm25_search(self, query: str, top_k: int = 10, policy_uin_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Performs BM25 Sparse Keyword Search."""
        if not self.chunks:
            return []

        q_tokens = self._tokenize(query)
        num_docs = len(self.chunks)
        scores = np.zeros(num_docs, dtype=np.float32)

        for i, doc_toks in enumerate(self.doc_tokens):
            if policy_uin_filter and self.chunks[i].get("policy_uin") != policy_uin_filter:
                continue

            doc_len = self.doc_lens[i]
            tf_dict: Dict[str, int] = {}
            for t in doc_toks:
                tf_dict[t] = tf_dict.get(t, 0) + 1

            score = 0.0
            for qt in q_tokens:
                if qt in tf_dict:
                    tf = tf_dict[qt]
                    idf_val = self.idf.get(qt, 0.0)
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                    score += idf_val * (numerator / denominator)

            # Header match boost for section precision
            header_str = self.chunks[i].get("header_path", "").lower()
            header_matches = sum(1 for qt in q_tokens if qt in header_str and qt not in ["lic", "policy", "plan", "uin"])
            if header_matches > 0:
                score *= (1.0 + 2.0 * header_matches)

            scores[i] = score

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if scores[idx] > 0 or not policy_uin_filter:
                results.append({"chunk": self.chunks[idx], "bm25_score": float(scores[idx]), "idx": int(idx)})
        return results

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        policy_uin_filter: Optional[str] = None,
        policy_name_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Dense Vector Cosine Similarity search."""
        if self.embeddings is None or len(self.embeddings) == 0 or not self.chunks:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        scores = np.dot(self.embeddings, q_vec)

        filtered_indices = []
        for idx, chunk in enumerate(self.chunks):
            if policy_uin_filter and chunk.get("policy_uin") != policy_uin_filter:
                continue
            if policy_name_filter and policy_name_filter.lower() not in chunk.get("policy_name", "").lower():
                continue
            filtered_indices.append(idx)

        if not filtered_indices:
            return []

        sorted_filtered = sorted(filtered_indices, key=lambda i: scores[i], reverse=True)
        top_indices = sorted_filtered[:top_k]

        return [{"chunk": self.chunks[idx], "score": float(scores[idx]), "idx": int(idx)} for idx in top_indices]

    def hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int = 5,
        policy_uin_filter: Optional[str] = None,
        rrf_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Hybrid Retrieval combining Dense Vector Similarity + BM25 Keyword Search
        using Reciprocal Rank Fusion (RRF).
        """
        candidate_k = max(20, top_k * 5)
        dense_results = self.search(query_embedding, top_k=candidate_k, policy_uin_filter=policy_uin_filter)
        bm25_results = self.bm25_search(query, top_k=candidate_k, policy_uin_filter=policy_uin_filter)

        rrf_scores: Dict[int, float] = {}

        # Dense ranks
        for rank, res in enumerate(dense_results, 1):
            idx = res["idx"]
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (rrf_k + rank))

        # BM25 ranks (weighted higher for exact term precision)
        for rank, res in enumerate(bm25_results, 1):
            idx = res["idx"]
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 2.0 * (1.0 / (rrf_k + rank))

        sorted_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)[:top_k]

        return [{
            "chunk": self.chunks[idx],
            "rrf_score": float(rrf_scores[idx])
        } for idx in sorted_indices]

    def save(self, directory: str):
        """Saves vector store index (metadata JSON + embeddings numpy array) to disk."""
        os.makedirs(directory, exist_ok=True)
        meta_path = os.path.join(directory, "metadata.json")
        emb_path = os.path.join(directory, "embeddings.npy")

        with open(meta_path, "w", encoding="utf-8") as wf:
            json.dump(self.chunks, wf, indent=2, ensure_ascii=False)

        if self.embeddings is not None:
            np.save(emb_path, self.embeddings)

    def load(self, directory: str):
        """Loads vector store index from disk."""
        meta_path = os.path.join(directory, "metadata.json")
        emb_path = os.path.join(directory, "embeddings.npy")

        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as rf:
                self.chunks = json.load(rf)

        if os.path.exists(emb_path):
            self.embeddings = np.load(emb_path)

        if self.chunks:
            self._build_bm25_index()
