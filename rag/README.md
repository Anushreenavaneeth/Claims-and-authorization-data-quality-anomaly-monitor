# RAG (Retrieval-Augmented Generation) System

Provides AI-driven investigations by linking active anomalies with standard remediation procedures (SOPs).

## Architecture
1. **Ingestion (`ingestion/`)**: Loads, chunks, and writes troubleshooting SOP files into Vector DB.
2. **Vector Store (`retrieval/`)**: Manages ChromaDB instances and indexes.
3. **Reasoning (`generation/`)**: Constructs prompt context with vectors and queries OpenAI/Gemini models to get remediation text.
