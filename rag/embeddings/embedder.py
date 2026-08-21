"""
Embedding generation utilities for the RAG system.
"""

from typing import List

from sentence_transformers import SentenceTransformer

from .config import (
    EMBEDDING_MODEL_NAME,
    BATCH_SIZE
)


class DocumentEmbedder:
    """
    Generates vector embeddings for document chunks.
    """

    def __init__(
        self,
        model_name: str = EMBEDDING_MODEL_NAME
    ):
        self.model_name = model_name

        print(
            f"Loading embedding model: {self.model_name}"
        )

        self.model = SentenceTransformer(
            self.model_name
        )

        print("Embedding model loaded successfully.")

    def embed_texts(
        self,
        texts: List[str]
    ):
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text chunks.

        Returns:
            Embedding matrix.
        """

        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embeddings

    def embed_single(
        self,
        text: str
    ):
        """
        Generate an embedding for a single text.
        """

        if not text or not text.strip():
            raise ValueError(
                "Cannot generate embedding for empty text."
            )

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embedding

    def get_dimension(self) -> int:
        """
        Return embedding vector dimension.
        """

        return self.model.get_sentence_embedding_dimension()