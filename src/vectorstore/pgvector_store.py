import os
import logging
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("pgvector_store")

class PGVectorStore:
    """
    Vector Store implementation backed by GCP Cloud SQL PostgreSQL with pgvector extension.
    Executes native 768-dimensional vector cosine distance search (`<=>` operator).
    """
    def __init__(
        self,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        dbname: Optional[str] = None,
        port: int = 5432
    ):
        self.host = host or os.getenv("DB_HOST", "34.100.195.31")
        self.user = user or os.getenv("DB_USER", "lic_admin")
        self.password = password or os.getenv("DB_PASSWORD", "6mKZ0d1ULXOAYGjk")
        self.dbname = dbname or os.getenv("DB_NAME", "lic_rag_db")
        self.port = int(port or os.getenv("DB_PORT", "5432"))

    def _get_connection(self):
        return psycopg2.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            dbname=self.dbname,
            port=self.port,
            cursor_factory=RealDictCursor
        )

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        policy_uin_filter: Optional[str] = None,
        policy_name_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes dense vector similarity search against policy_chunks table in Cloud SQL PostgreSQL pgvector.
        Returns top_k nearest chunk dictionaries with calculated cosine similarity score (1 - cosine_distance).
        """
        if not query_embedding:
            return []

        emb_str = f"[{','.join(map(str, query_embedding))}]"

        where_clauses = []
        params = [emb_str]

        if policy_uin_filter:
            where_clauses.append("policy_uin = %s")
            params.append(policy_uin_filter)

        if policy_name_filter:
            where_clauses.append("policy_name ILIKE %s")
            params.append(f"%{policy_name_filter}%")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Order by cosine distance (<=> operator) and compute cosine similarity
        query = f"""
            SELECT 
                chunk_id, policy_name, policy_uin, header_path, content,
                token_count, table_context, metadata_json,
                1 - (embedding <=> %s::vector) AS score
            FROM policy_chunks
            {where_sql}
            ORDER BY embedding <=> %s::vector
            LIMIT {int(top_k)};
        """

        # Append emb_str for the ORDER BY clause
        params.append(emb_str)

        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            results = []
            for r in rows:
                chunk_dict = dict(r["metadata_json"]) if r.get("metadata_json") else {
                    "chunk_id": r["chunk_id"],
                    "policy_name": r["policy_name"],
                    "policy_uin": r["policy_uin"],
                    "header_path": r["header_path"],
                    "content": r["content"],
                    "token_count": r["token_count"],
                    "table_context": r["table_context"]
                }
                results.append({
                    "chunk": chunk_dict,
                    "score": float(r["score"])
                })
            return results
        except Exception as e:
            logger.error(f"Error executing Cloud SQL pgvector search: {e}")
            return []
