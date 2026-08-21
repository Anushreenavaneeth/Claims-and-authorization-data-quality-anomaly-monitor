"""
RAG Service client.

Calls Charan's RAG microservice (http://localhost:8001) over HTTP.
The backend never imports sentence_transformers — clean separation.
"""

import os
from typing import Any, Dict, Optional

import httpx

RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8001")
_TIMEOUT = 30.0  # seconds


def is_available() -> bool:
    """Return True if the RAG microservice health check passes."""
    try:
        resp = httpx.get(f"{RAG_SERVICE_URL}/health", timeout=3.0)
        data = resp.json()
        return resp.status_code == 200 and data.get("status") == "ready"
    except Exception:  # noqa: BLE001
        return False


def get_recommendation(anomaly_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    POST the anomaly record to the RAG microservice.

    Returns the parsed JSON response, or None on any failure.
    """
    try:
        resp = httpx.post(
            f"{RAG_SERVICE_URL}/recommend",
            json=anomaly_record,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:  # noqa: BLE001
        return None
