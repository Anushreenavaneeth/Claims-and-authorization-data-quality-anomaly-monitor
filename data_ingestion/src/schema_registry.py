"""
schema_registry.py
-------------------
Loads every "*_schema.json" file in a config directory into a
{schema_name: schema_dict} registry, so schema_matcher.detect_schema() has
a full set of known schemas to compare an ingested file's columns against,
instead of the caller having to already know and hard-code the one right
schema file for each input.

Adding a new schema (e.g. "authorization_schema.json") to the config
directory is enough to make it a detection candidate — no code changes
needed elsewhere.
"""

import json
from pathlib import Path
from typing import Any, Dict


def load_schemas(schema_dir: str) -> Dict[str, Dict[str, Any]]:
    """
    Returns {schema_name: schema_dict} for every "<name>_schema.json" file
    found directly in schema_dir. E.g. "config/claims_schema.json" ->
    key "claims".
    """
    schemas: Dict[str, Dict[str, Any]] = {}
    directory = Path(schema_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"Schema directory not found: {schema_dir}")

    for path in sorted(directory.glob("*_schema.json")):
        name = path.stem
        if name.endswith("_schema"):
            name = name[: -len("_schema")]
        schemas[name] = json.loads(path.read_text(encoding="utf-8"))

    return schemas
