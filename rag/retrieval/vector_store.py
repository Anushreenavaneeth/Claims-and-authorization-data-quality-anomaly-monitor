"""
Vector store for loading and searching document embeddings.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

from .config import EMBEDDINGS_FILE


class VectorStore:
    """
    Simple JSON-based vector store.

    Loads pre-generated document embeddings and performs
    cosine similarity search.
    """

    def __init__(
        self,
        embeddings_file: Path = EMBEDDINGS_FILE
    ):
        self.embeddings_file = Path(
            embeddings_file
        )

        self.documents = []
        self.embeddings = None

        self._load()

    def _load(self):
        """
        Load document embeddings from JSON.
        """

        if not self.embeddings_file.exists():
            raise FileNotFoundError(
                f"Embedding file not found: "
                f"{self.embeddings_file}"
            )

        with open(
            self.embeddings_file,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not data:
            raise ValueError(
                "Embedding file is empty."
            )

        self.documents = data

        self.embeddings = np.array(
            [
                item["embedding"]
                for item in data
            ],
            dtype=np.float32
        )

        # Normalize vectors for cosine similarity.
        norms = np.linalg.norm(
            self.embeddings,
            axis=1,
            keepdims=True
        )

        norms[norms == 0] = 1

        self.embeddings = (
            self.embeddings / norms
        )

    def search(
        self,
        query_embedding,
        top_k: int = 5,
        similarity_threshold: float = 0.35
    ) -> List[Dict[str, Any]]:
        """
        Search for the most relevant document chunks.

        Args:
            query_embedding:
                Vector representation of the query.

            top_k:
                Maximum number of results.

            similarity_threshold:
                Minimum similarity required.

        Returns:
            Ranked list of relevant document chunks.
        """

        query_vector = np.asarray(
            query_embedding,
            dtype=np.float32
        )

        if query_vector.ndim != 1:
            query_vector = query_vector.flatten()

        norm = np.linalg.norm(
            query_vector
        )

        if norm == 0:
            raise ValueError(
                "Query embedding cannot be a zero vector."
            )

        query_vector = (
            query_vector / norm
        )

        # Cosine similarity because all vectors
        # are normalized.
        similarities = np.dot(
            self.embeddings,
            query_vector
        )

        ranked_indices = np.argsort(
            similarities
        )[::-1]

        results = []

        for index in ranked_indices[:top_k]:

            score = float(
                similarities[index]
            )

            if score < similarity_threshold:
                continue

            document = self.documents[
                int(index)
            ]

            results.append(
                {
                    "text": document["text"],
                    "metadata": document.get(
                        "metadata",
                        {}
                    ),
                    "similarity_score": score
                }
            )

        return results

    def count(self) -> int:
        """
        Return number of stored document chunks.
        """

        return len(self.documents)

    def dimension(self) -> int:
        """
        Return embedding dimension.
        """

        if self.embeddings is None:
            return 0

        return self.embeddings.shape[1]