FROM python:3.10-slim

WORKDIR /app

# Backend Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ML pipeline dependencies (for authorization/claims/pharmacy inference)
COPY ml/requirements.txt ./ml_requirements.txt
RUN pip install --no-cache-dir -r ml_requirements.txt || true

# Application source
COPY backend/app ./app

# ML model artefacts & pipeline code (needed for run-time inference)
COPY ml/ ./ml/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
