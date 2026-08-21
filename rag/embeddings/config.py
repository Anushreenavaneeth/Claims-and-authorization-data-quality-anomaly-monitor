"""
Configuration for the RAG embedding pipeline.
"""

from pathlib import Path


# ---------------------------------------------------------
# Project Paths
# ---------------------------------------------------------

RAG_DIR = Path(__file__).resolve().parent.parent

DOCUMENTS_DIR = RAG_DIR / "documents"

EMBEDDINGS_DIR = RAG_DIR / "embeddings"

VECTOR_STORE_DIR = EMBEDDINGS_DIR / "vector_store"


# ---------------------------------------------------------
# Embedding Model
# ---------------------------------------------------------

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

EMBEDDING_DIMENSION = 384


# ---------------------------------------------------------
# Chunking Configuration
# ---------------------------------------------------------

CHUNK_SIZE = 800

CHUNK_OVERLAP = 120


# ---------------------------------------------------------
# Supported Document Types
# ---------------------------------------------------------

SUPPORTED_EXTENSIONS = {
    ".md",
    ".txt"
}


# ---------------------------------------------------------
# Runtime Configuration
# ---------------------------------------------------------

BATCH_SIZE = 32


# ---------------------------------------------------------
# Create Required Directories
# ---------------------------------------------------------

EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)