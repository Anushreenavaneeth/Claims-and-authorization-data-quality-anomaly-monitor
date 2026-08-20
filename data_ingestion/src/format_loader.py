"""
format_loader.py
-----------------
Multi-format ingestion loader for the Data Ingestion & Validation module.

Detects the input file's format and normalizes it into a pandas DataFrame
(all string dtype, matching your existing loader.py convention) that flows
straight into the existing schema-driven validator.py.

Supported formats: csv, xlsx/xls, json, yml/yaml, pdf, image (png/jpg/jpeg)

Usage:
    from format_loader import load_any

    df, meta = load_any("incoming/claims_batch_07.pdf")
    if meta["status"] != "ok":
        # route to manual review / log and skip
        ...
    else:
        # hand off to your existing validator
        result = validator.validate(df, schema)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Tuple

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


class FormatDetectionError(Exception):
    """Raised when the input format cannot be determined at all."""


SUPPORTED_EXTENSIONS = {
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
}

# Keys we'll look under if a JSON/YAML file wraps its records in an envelope,
# e.g. {"claims": [...]} instead of a bare list.
RECORD_WRAPPER_KEYS = ("records", "data", "claims", "pharmacy", "items")


# --------------------------------------------------------------------------
# Format detection
# --------------------------------------------------------------------------

def detect_format(file_path: str) -> str:
    """Extension-based detection first; falls back to magic-byte sniffing
    for mislabeled or extension-less files."""
    ext = Path(file_path).suffix.lower()
    if ext in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[ext]

    with open(file_path, "rb") as f:
        head = f.read(8)

    if head[:4] == b"%PDF":
        return "pdf"
    if head[:2] == b"PK":  # xlsx is a zip container
        return "xlsx"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "image"
    if head[:2] == b"\xff\xd8":  # JPEG
        return "image"
    if head[:1] in (b"{", b"["):
        return "json"

    raise FormatDetectionError(
        f"Could not determine format for '{file_path}' from extension or content."
    )


# --------------------------------------------------------------------------
# Loaders — each returns a string-typed DataFrame or raises with a clear reason
# --------------------------------------------------------------------------

def load_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, dtype=str)
    return df.reset_index(drop=True)


def load_xlsx(file_path: str) -> pd.DataFrame:
    df = pd.read_excel(file_path, dtype=str, engine="openpyxl")
    return df.reset_index(drop=True)


def _unwrap_records(data: Any) -> list:
    """Normalize dict-wrapped or bare-object payloads into a list of records."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in RECORD_WRAPPER_KEYS:
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]  # single record
    raise ValueError("Payload is neither a list nor a dict of records.")


def load_json(file_path: str) -> pd.DataFrame:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = _unwrap_records(data)
    df = pd.DataFrame(records)
    return df.astype(str).reset_index(drop=True)


def load_yaml(file_path: str) -> pd.DataFrame:
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    records = _unwrap_records(data)
    df = pd.DataFrame(records)
    return df.astype(str).reset_index(drop=True)


def load_pdf(file_path: str) -> pd.DataFrame:
    """Extracts tables from a text-based PDF. Scanned/image PDFs won't yield
    tables here — those should be routed to load_image() instead."""
    try:
        import pdfplumber
    except ImportError as e:
        raise RuntimeError(
            "pdfplumber not installed. Add to requirements.txt: pdfplumber"
        ) from e

    tables = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table or len(table) < 2:
                    continue
                header, *rows = table
                tables.append(pd.DataFrame(rows, columns=header))

    if not tables:
        raise ValueError(
            f"No tables detected in '{file_path}'. If this is a scanned/"
            "image-based PDF, convert pages to images and use load_image()."
        )

    df = pd.concat(tables, ignore_index=True)
    return df.astype(str)


def load_image(file_path: str) -> pd.DataFrame:
    """Best-effort OCR table extraction. Low reliability — callers should
    treat a successful parse here as lower-confidence than structured formats."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(
            "pytesseract/Pillow not installed. Add to requirements.txt: "
            "pytesseract, Pillow. Also requires the tesseract-ocr system "
            "binary (e.g. `apt-get install tesseract-ocr` on the EC2 host)."
        ) from e

    text = pytesseract.image_to_string(Image.open(file_path))
    rows = [line.split() for line in text.splitlines() if line.strip()]

    if len(rows) < 2:
        raise ValueError(
            f"OCR on '{file_path}' did not yield a table-like structure. "
            "Route to manual review rather than auto-validation."
        )

    header, *data_rows = rows
    ncols = len(header)
    # Drop OCR noise rows that don't match the header's column count
    data_rows = [r for r in data_rows if len(r) == ncols]
    if not data_rows:
        raise ValueError(f"OCR on '{file_path}' produced a header but no matching rows.")

    df = pd.DataFrame(data_rows, columns=header)
    return df.astype(str)


LOADERS = {
    "csv": load_csv,
    "xlsx": load_xlsx,
    "json": load_json,
    "yaml": load_yaml,
    "pdf": load_pdf,
    "image": load_image,
}

# Formats where a successful parse still deserves a lower trust flag
LOW_CONFIDENCE_FORMATS = {"pdf", "image"}


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------

def load_any(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Detect format, load into a normalized string-typed DataFrame, and return
    metadata describing what happened. Never raises — failures are reported
    in metadata so the caller can route to a manual-review queue instead of
    crashing the batch.

    Returns:
        (df, metadata) where metadata has keys:
            source_file, detected_format, status ("ok" | "empty" | "failed"),
            confidence ("high" | "low"), warning, row_count, columns
    """
    metadata: Dict[str, Any] = {
        "source_file": file_path,
        "detected_format": None,
        "status": "failed",
        "confidence": "high",
        "warning": None,
        "row_count": 0,
        "columns": [],
    }

    try:
        fmt = detect_format(file_path)
    except FormatDetectionError as e:
        metadata["warning"] = str(e)
        return pd.DataFrame(), metadata

    metadata["detected_format"] = fmt
    metadata["confidence"] = "low" if fmt in LOW_CONFIDENCE_FORMATS else "high"

    try:
        df = LOADERS[fmt](file_path)
    except Exception as e:
        logger.error("Failed to load '%s' as %s: %s", file_path, fmt, e)
        metadata["warning"] = str(e)
        return pd.DataFrame(), metadata

    if df.empty:
        metadata["status"] = "empty"
        metadata["warning"] = "Parsed successfully but produced zero rows."
    else:
        metadata["status"] = "ok"

    metadata["row_count"] = len(df)
    metadata["columns"] = list(df.columns)
    return df, metadata