"""
Document chunking utilities for the RAG embedding pipeline.
"""

from typing import List, Dict


def chunk_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120
) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Document text.
        chunk_size: Maximum number of characters per chunk.
        chunk_overlap: Number of overlapping characters.

    Returns:
        List of text chunks.
    """

    if not text or not text.strip():
        return []

    text = text.strip()

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(start + chunk_size, text_length)

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - chunk_overlap

    return chunks


def create_chunks(
    documents: List[Dict],
    chunk_size: int = 800,
    chunk_overlap: int = 120
) -> List[Dict]:
    """
    Convert loaded documents into chunk records.

    Each chunk retains metadata from its source document.

    Args:
        documents: List of loaded document dictionaries.

    Returns:
        List of chunk dictionaries.
    """

    chunked_documents = []

    for document in documents:

        text = document.get("content", "")
        metadata = document.get("metadata", {})

        chunks = chunk_text(
            text=text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        for index, chunk in enumerate(chunks):

            chunked_documents.append(
                {
                    "text": chunk,
                    "metadata": {
                        **metadata,
                        "chunk_id": index
                    }
                }
            )

    return chunked_documents