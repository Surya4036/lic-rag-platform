import os
import re
import hashlib
import numpy as np
from typing import List, Optional

class PolicyEmbedder:
    """
    Embedding pipeline provider for LIC Policy documents.
    Supports GCP Vertex AI / Gemini API (text-embedding-004) when API key is available,
    and a local deterministic normalized feature vectorizer fallback for offline development.
    """
    def __init__(self, dimension: int = 768, force_local: bool = False):
        self.dimension = dimension
        self.force_local = force_local
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.gcp_project = os.environ.get("GCP_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
        self.gcp_location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
        self._genai_client = None

        if not self.force_local:
            try:
                from google import genai
                if self.api_key:
                    self._genai_client = genai.Client(api_key=self.api_key)
                elif self.gcp_project:
                    # Vertex AI mode using Application Default Credentials (ADC) in us-central1
                    self._genai_client = genai.Client(vertexai=True, project=self.gcp_project, location=self.gcp_location)
            except Exception:
                self._genai_client = None

    def _local_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic L2-normalized 768-dim feature vector
        based on word/n-gram hashing for local offline similarity search.
        """
        tokens = re.findall(r"\w+", text.lower())
        vec = np.zeros(self.dimension, dtype=np.float32)

        # Hash individual tokens and token bigrams
        for i, token in enumerate(tokens):
            # Unigram
            h1 = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.dimension
            vec[h1] += 1.0

            # Bigram
            if i > 0:
                bigram = f"{tokens[i-1]}_{token}"
                h2 = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16) % self.dimension
                vec[h2] += 1.5

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            # Fallback uniform unit vector
            vec = np.ones(self.dimension, dtype=np.float32) / np.sqrt(self.dimension)

        return vec.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a list of text strings."""
        if not texts:
            return []

        if self._genai_client and not self.force_local:
            try:
                # Vertex AI / Gemini Text Embeddings API
                response = self._genai_client.models.embed_content(
                    model="text-embedding-004",
                    contents=texts
                )
                if hasattr(response, "embeddings"):
                    return [e.values for e in response.embeddings]
            except Exception as e:
                # Log or fallback to local embedder if API fails
                pass

        # Fallback local deterministic embedding
        return [self._local_embedding(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        """Generates embedding vector for a single query string."""
        results = self.embed_texts([query])
        return results[0] if results else self._local_embedding(query)
