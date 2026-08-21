# RAG (Retrieval-Augmented Generation) Architecture

To support operations workers in resolving data quality issues quickly:
1. **Ingestion**: SOPs (Standard Operating Procedures) are chunked and vectorized.
2. **Retrieval**: When an anomaly is inspected, relevant pipeline SOPs are pulled.
3. **Generation**: The context is combined with anomaly parameters to generate explanation summaries and recommendations.
