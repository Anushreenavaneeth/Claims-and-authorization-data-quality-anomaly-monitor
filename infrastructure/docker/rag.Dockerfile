FROM python:3.11-slim

WORKDIR /app

# Install curl for health-check probe
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install RAG dependencies
COPY rag/requirements.txt ./rag_requirements.txt
RUN pip install --no-cache-dir -r rag_requirements.txt

# Copy RAG source and ML artefacts needed at runtime
COPY rag/ ./rag/
COPY ml/ ./ml/

EXPOSE 8001

CMD ["python", "-m", "rag.serve"]
