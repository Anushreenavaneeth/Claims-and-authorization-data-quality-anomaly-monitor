from pathlib import Path
import pandas as pd

def load_csv(file_path):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if path.suffix.lower() != ".csv":
        raise ValueError("Only CSV files are supported currently.")
    # Read everything as raw strings so pandas doesn't silently infer types
    # (e.g. dropping leading zeros from codes/IDs like "00123"). Validator.py
    # is responsible for coercing to numeric/date types as needed per schema.
    df = pd.read_csv(path, dtype=str, keep_default_na=True)
    return df.reset_index(drop=True)
