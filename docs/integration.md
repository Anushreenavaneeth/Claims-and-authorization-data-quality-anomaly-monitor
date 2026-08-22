# Integration Architecture

## Overview

The integration layer connects the three independent ML pipelines (Claims, Authorization, Pharmacy) into one unified platform through a common schema, one SLA engine, and one RAG recommendation layer.

## Data Flow

```
CLAIMS JSON         AUTHORIZATION JSON      PHARMACY JSON
     ↓                      ↓                      ↓
claims_adapter      authorization_adapter   pharmacy_adapter
     ↓                      ↓                      ↓
     └──────────────────────┴──────────────────────┘
                             ↓
                    StandardAnomalyRecord
                    (common_schema.py)
                             ↓
                    Common SLA Engine
                    (sla_engine.py)
                             ↓
                    SLA-enriched Record
                             ↓
                    RAG Connector
                    (rag_connector.py)
                             ↓
                    Final JSON (persisted to SQLite)
                             ↓
                    Backend API → Frontend Dashboard
```

## Files

| File | Purpose |
|------|---------|
| `integration/common_schema.py` | Standardized dataclass schema for all datasets |
| `integration/claims_adapter.py` | Converts claims JSON → StandardAnomalyRecord |
| `integration/authorization_adapter.py` | Converts authorization JSON → StandardAnomalyRecord |
| `integration/pharmacy_adapter.py` | Converts pharmacy JSON → StandardAnomalyRecord |
| `integration/sla_engine.py` | ONE common SLA engine for all datasets |
| `integration/rag_connector.py` | Bridges StandardAnomalyRecord → RAG → RAGBlock |
| `integration/orchestrator.py` | Main entry point; persists to SQLite |
| `config/sla_config.json` | All SLA thresholds — edit here, not in code |

## Running the Pipeline

```bash
# All datasets
python integration/orchestrator.py all

# Single dataset
python integration/orchestrator.py claims
python integration/orchestrator.py authorization
python integration/orchestrator.py pharmacy

# With record limit (testing)
python integration/orchestrator.py claims 100
```

## API Trigger

```http
POST /api/process
Authorization: Bearer <admin_token>
Content-Type: application/json

{"dataset": "claims"}   # or "authorization", "pharmacy", or omit for all
```
