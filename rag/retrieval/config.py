"""
Configuration for the RAG retrieval pipeline.
"""

from pathlib import Path


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

RAG_DIR = Path(__file__).resolve().parent.parent

VECTOR_STORE_DIR = (
    RAG_DIR /
    "embeddings" /
    "vector_store"
)

EMBEDDINGS_FILE = (
    VECTOR_STORE_DIR /
    "document_embeddings.json"
)


# ---------------------------------------------------------
# Retrieval Configuration
# ---------------------------------------------------------

TOP_K = 5

SIMILARITY_THRESHOLD = 0.35


# ---------------------------------------------------------
# Embedding Model
# ---------------------------------------------------------

EMBEDDING_MODEL_NAME = (
    "sentence-transformers/all-MiniLM-L6-v2"
)