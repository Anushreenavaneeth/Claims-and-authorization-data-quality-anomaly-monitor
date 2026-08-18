# Healthcare Data Operations Platform

A modern, AI-powered platform for monitoring data quality and detecting anomalies in healthcare claims, pharmacy prescriptions, and pre-authorizations.

## Tech Stack
* **Frontend**: React + TypeScript + Tailwind CSS + Vite
* **Backend**: FastAPI + Python + SQLAlchemy + PostgreSQL + Redis
* **Realtime**: WebSockets for live telemetry
* **ML**: Anomaly Detection, Root Cause Analysis, and SLA Prediction models
* **RAG**: LLM-powered SOP retrieval, explanations, and remediation recommendations

## Get Started
1. Configure environment variables in `.env` (copy `.env.example`).
2. Run backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
3. Run frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Run Docker compose for all services:
   ```bash
   docker-compose up --build
   ```
