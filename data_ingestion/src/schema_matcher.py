"""
schema_matcher.py
------------------
Solves two related problems that used to make validator.py mark good data
as invalid:

1. Column-name tolerance: a source file's column names rarely match the
   schema's canonical names exactly (e.g. "ClaimID" vs "claim_id" vs
   "Claim Number"). resolve_columns() maps incoming columns onto a schema's
   canonical names via, in order:
     a) exact match after normalization (case/spacing/punctuation only)
     b) alias lookup (schema-defined synonyms, "column_aliases" in the
        schema JSON)
     c) fuzzy string match as a last-resort fallback (stdlib difflib,
        no extra dependency)

2. Schema auto-detection: given an ingested file's columns, figure out
   which schema (claims, pharmacy, ...) it actually matches, instead of
   the caller having to already know and hard-code that mapping.

Nothing here changes validator.py's actual validation rules (required
columns, types, ranges, etc). This only decides *which* schema applies to
a file and *how its columns map* onto that schema's canonical names before
the existing rules run, unchanged, on the renamed DataFrame.
"""

import difflib
import re
from typing import Any, Dict, List, Tuple

# difflib.SequenceMatcher ratio cutoff for the fuzzy fallback. Tuned to catch
# case/typo/punctuation variants (e.g. "claimid" vs "claim_id" ~0.93,
# "prescription_dt" vs "prescription_date" ~0.94) without over-matching
# unrelated short column names against each other.
FUZZY_THRESHOLD = 0.82


def normalize_name(name: str) -> str:
    """Collapses 'Claim ID', 'claimId', 'CLAIM_ID', 'claim-id' etc. into the
    same token, e.g. 'claim_id'."""
    s = str(name).strip().lower()
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def _alias_vocabulary(schema: Dict[str, Any]) -> Dict[str, str]:
    """Builds {normalized_name_or_alias: canonical_column} for every
    required column, including the canonical name itself plus any
    schema-defined aliases (schema["column_aliases"][col] = [...])."""
    vocab: Dict[str, str] = {}
    aliases_cfg = schema.get("column_aliases", {})
    for col in schema.get("required_columns", []):
        vocab[normalize_name(col)] = col
        for alias in aliases_cfg.get(col, []):
            vocab[normalize_name(alias)] = col
    return vocab


def resolve_columns(
    columns: List[str],
    schema: Dict[str, Any],
    fuzzy_threshold: float = FUZZY_THRESHOLD,
) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
    """
    Maps a DataFrame's actual column names onto a schema's canonical
    required-column names.

    Returns:
        mapping: {original_column_name: canonical_name} for columns that
            were matched. Unmatched columns are simply absent here, so
            they fall through to "unexpected column" handling downstream,
            exactly as before.
        resolution_log: one entry per column that was matched to a
            *different* name than its canonical form, describing how
            (method: "alias" | "fuzzy") and with what confidence, so the
            validation report stays transparent instead of silently
            renaming things.
    """
    vocab = _alias_vocabulary(schema)
    mapping: Dict[str, str] = {}
    resolution_log: List[Dict[str, Any]] = []
    claimed_canonicals = set()

    # Pass 1: exact / alias match on normalized names.
    remaining = []
    for col in columns:
        norm = normalize_name(col)
        canonical = vocab.get(norm)
        if canonical is not None and canonical not in claimed_canonicals:
            mapping[col] = canonical
            claimed_canonicals.add(canonical)
            if col != canonical:
                method = "exact" if norm == normalize_name(canonical) else "alias"
                resolution_log.append({
                    "original_column": col,
                    "matched_to": canonical,
                    "method": method,
                    "confidence": 1.0,
                })
        else:
            remaining.append(col)

    # Pass 2: fuzzy fallback for anything still unmatched, only against
    # canonical names/aliases whose canonical hasn't already been claimed
    # (so two source columns can't both fuzzy-collide onto the same field).
    available_keys = [k for k, canon in vocab.items() if canon not in claimed_canonicals]
    for col in remaining:
        if not available_keys:
            break
        norm = normalize_name(col)
        close = difflib.get_close_matches(norm, available_keys, n=1, cutoff=fuzzy_threshold)
        if not close:
            continue
        matched_key = close[0]
        canonical = vocab[matched_key]
        score = difflib.SequenceMatcher(None, norm, matched_key).ratio()
        mapping[col] = canonical
        claimed_canonicals.add(canonical)
        available_keys = [k for k in available_keys if vocab[k] != canonical]
        resolution_log.append({
            "original_column": col,
            "matched_to": canonical,
            "method": "fuzzy",
            "confidence": round(score, 3),
        })

    return mapping, resolution_log


def apply_column_resolution(df, schema):
    """Returns (renamed_df, resolution_log). Matched columns are renamed to
    their schema canonical form; unmatched columns pass through untouched
    (still surfaced as "unexpected columns" by validator.py, same as
    before this change)."""
    mapping, resolution_log = resolve_columns(list(df.columns), schema)
    renamed = df.rename(columns=mapping)
    return renamed, resolution_log


def score_schema_match(columns: List[str], schema: Dict[str, Any]) -> Dict[str, Any]:
    """How well do these columns match this one schema? score = fraction of
    the schema's required columns that could be resolved (exact/alias/fuzzy)
    from the given columns."""
    required = schema.get("required_columns", [])
    if not required:
        return {"score": 0.0, "matched": 0, "required": 0, "resolution_log": []}
    mapping, resolution_log = resolve_columns(columns, schema)
    matched_canonicals = set(mapping.values())
    matched = sum(1 for c in required if c in matched_canonicals)
    return {
        "score": matched / len(required),
        "matched": matched,
        "required": len(required),
        "resolution_log": resolution_log,
    }


def detect_schema(
    columns: List[str],
    schemas: Dict[str, Dict[str, Any]],
    min_confidence: float = 0.6,
) -> Dict[str, Any]:
    """
    Given a file's columns and a {schema_name: schema_dict} registry, picks
    the best-matching schema instead of assuming the caller already knows.

    Returns:
        {
          "matched_schema": str | None,   # None if nothing clears min_confidence
          "confidence": float,            # winning score, or best score if none matched
          "candidates": [{"schema", "score", "matched", "required"}, ...],  # all, sorted desc
          "resolution_log": [...],        # column resolution detail for the winning schema
        }
    """
    candidates = []
    per_schema_logs = {}
    for name, schema in schemas.items():
        result = score_schema_match(columns, schema)
        candidates.append({
            "schema": name,
            "score": round(result["score"], 3),
            "matched": result["matched"],
            "required": result["required"],
        })
        per_schema_logs[name] = result["resolution_log"]

    candidates.sort(key=lambda c: c["score"], reverse=True)

    if not candidates or candidates[0]["score"] < min_confidence:
        return {
            "matched_schema": None,
            "confidence": candidates[0]["score"] if candidates else 0.0,
            "candidates": candidates,
            "resolution_log": [],
        }

    best = candidates[0]
    return {
        "matched_schema": best["schema"],
        "confidence": best["score"],
        "candidates": candidates,
        "resolution_log": per_schema_logs[best["schema"]],
    }
