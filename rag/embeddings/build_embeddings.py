"""
Main embedding pipeline.

Flow:

Documents
    ↓
Document Loader
    ↓
Chunking
    ↓
Embedding Model
    ↓
Vector Embeddings
"""

import json
from pathlib import Path

from ..document_loader import load_documents

from .config import (
    DOCUMENTS_DIR,
    VECTOR_STORE_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL_NAME
)

from .chunker import create_chunks

from .embedder import DocumentEmbedder


def save_embeddings(
    chunks,
    embeddings,
    output_path: Path
):
    """
    Save chunks and embeddings together.

    The embeddings are converted to lists so they can
    be serialized into JSON.
    """

    records = []

    for chunk, embedding in zip(chunks, embeddings):

        records.append(
            {
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "embedding": embedding.tolist()
            }
        )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            ensure_ascii=False
        )


def main():

    print("=" * 60)
    print("RAG EMBEDDING PIPELINE")
    print("=" * 60)

    # -----------------------------------------------------
    # 1. Load Documents
    # -----------------------------------------------------

    print("\n[1/4] Loading documents...")

    documents = load_documents(
        DOCUMENTS_DIR
    )

    print(
        f"Documents loaded: {len(documents)}"
    )

    if not documents:
        print(
            "No documents found."
        )
        return

    # -----------------------------------------------------
    # 2. Create Chunks
    # -----------------------------------------------------

    print("\n[2/4] Creating document chunks...")

    chunks = create_chunks(
        documents=documents,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    print(
        f"Chunks created: {len(chunks)}"
    )

    if not chunks:
        print(
            "No chunks were created."
        )
        return

    # -----------------------------------------------------
    # 3. Generate Embeddings
    # -----------------------------------------------------

    print("\n[3/4] Generating embeddings...")

    embedder = DocumentEmbedder(
        model_name=EMBEDDING_MODEL_NAME
    )

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = embedder.embed_texts(
        texts
    )

    dimension = embedder.get_dimension()

    print(
        f"Embedding dimension: {dimension}"
    )

    # -----------------------------------------------------
    # 4. Save Embeddings
    # -----------------------------------------------------

    print("\n[4/4] Saving embeddings...")

    output_path = (
        VECTOR_STORE_DIR /
        "document_embeddings.json"
    )

    save_embeddings(
        chunks=chunks,
        embeddings=embeddings,
        output_path=output_path
    )

    print(
        f"Embeddings saved to:\n{output_path}"
    )

    print("\n" + "=" * 60)
    print("EMBEDDING PIPELINE COMPLETED")
    print("=" * 60)

    print(
        f"\nDocuments : {len(documents)}"
    )

    print(
        f"Chunks    : {len(chunks)}"
    )

    print(
        f"Dimension : {dimension}"
    )

    print(
        f"Model     : {EMBEDDING_MODEL_NAME}"
    )


if __name__ == "__main__":
    main()