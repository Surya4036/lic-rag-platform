import os
import json
import logging
import numpy as np
import psycopg2
from psycopg2.extras import execute_values, Json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("migrate_pgvector")

DB_HOST = os.getenv("DB_HOST", "34.100.195.31")
DB_USER = os.getenv("DB_USER", "lic_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "6mKZ0d1ULXOAYGjk")
DB_NAME = os.getenv("DB_NAME", "lic_rag_db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))

VECTOR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vector_store")

def migrate():
    meta_path = os.path.join(VECTOR_DIR, "metadata.json")
    emb_path = os.path.join(VECTOR_DIR, "embeddings.npy")

    if not os.path.exists(meta_path) or not os.path.exists(emb_path):
        logger.error(f"Vector store files not found at {VECTOR_DIR}")
        return

    with open(meta_path, "r", encoding="utf-8") as f:
        meta_data = json.load(f)
        chunks = meta_data.get("chunks", [])

    embeddings = np.load(emb_path)

    logger.info(f"Loaded {len(chunks)} chunks and embeddings matrix shape {embeddings.shape}")

    logger.info(f"Connecting to Cloud SQL PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}...")
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
        port=DB_PORT
    )
    cur = conn.cursor()

    # 1. Enable pgvector extension
    logger.info("Ensuring pgvector extension is enabled...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create policy_chunks table
    logger.info("Creating policy_chunks schema in Cloud SQL PostgreSQL...")
    cur.execute("""
        DROP TABLE IF EXISTS policy_chunks;
        CREATE TABLE policy_chunks (
            id SERIAL PRIMARY KEY,
            chunk_id VARCHAR(100) UNIQUE NOT NULL,
            policy_name VARCHAR(255),
            policy_uin VARCHAR(100),
            header_path TEXT,
            content TEXT,
            token_count INT,
            table_context TEXT,
            metadata_json JSONB,
            embedding vector(768)
        );
    """)

    # 3. Create Vector Index for fast Cosine Distance Search
    logger.info("Creating HNSW vector index for pgvector...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS policy_chunks_embedding_hnsw_idx 
        ON policy_chunks 
        USING hnsw (embedding vector_cosine_ops);
    """)

    # 4. Insert chunks & embeddings
    logger.info("Inserting chunks and embeddings into Cloud SQL PostgreSQL...")
    insert_sql = """
        INSERT INTO policy_chunks (
            chunk_id, policy_name, policy_uin, header_path, content,
            token_count, table_context, metadata_json, embedding
        ) VALUES %s
        ON CONFLICT (chunk_id) DO UPDATE SET
            policy_name = EXCLUDED.policy_name,
            policy_uin = EXCLUDED.policy_uin,
            header_path = EXCLUDED.header_path,
            content = EXCLUDED.content,
            token_count = EXCLUDED.token_count,
            table_context = EXCLUDED.table_context,
            metadata_json = EXCLUDED.metadata_json,
            embedding = EXCLUDED.embedding;
    """

    rows = []
    for i, chunk in enumerate(chunks):
        emb_list = embeddings[i].tolist()
        # Convert vector float list to string format for pgvector '[0.1, 0.2, ...]'
        emb_str = f"[{','.join(map(str, emb_list))}]"
        rows.append((
            chunk.get("chunk_id", f"chunk_{i}"),
            chunk.get("policy_name", ""),
            chunk.get("policy_uin", ""),
            chunk.get("header_path", ""),
            chunk.get("content", ""),
            chunk.get("token_count", 0),
            chunk.get("table_context", ""),
            Json(chunk),
            emb_str
        ))

    execute_values(cur, insert_sql, rows)
    conn.commit()

    # 5. Verify insertion count
    cur.execute("SELECT COUNT(*) FROM policy_chunks;")
    count = cur.fetchone()[0]
    logger.info(f"Successfully migrated {count} chunks into Cloud SQL PostgreSQL pgvector database!")

    # 6. Test Vector Similarity Query
    test_vec = embeddings[0].tolist()
    test_vec_str = f"[{','.join(map(str, test_vec))}]"
    cur.execute("""
        SELECT chunk_id, policy_name, header_path, 1 - (embedding <=> %s::vector) AS similarity
        FROM policy_chunks
        ORDER BY embedding <=> %s::vector
        LIMIT 3;
    """, (test_vec_str, test_vec_str))
    results = cur.fetchall()

    logger.info("--- Cloud SQL pgvector Similarity Test Results ---")
    for r in results:
        logger.info(f"Chunk ID: {r[0]} | Policy: {r[1]} | Similarity: {r[3]:.4f} | Header: {r[2]}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate()
