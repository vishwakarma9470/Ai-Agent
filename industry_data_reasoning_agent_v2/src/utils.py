
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

import numpy as np
import pandas as pd


def normalize_col(col: str) -> str:
    return str(col).strip().replace(" ", "_").replace("-", "_").replace("/", "_").lower()


def safe_json(obj: Any, max_chars: int = 20000) -> str:
    def default(o: Any) -> Any:
        if isinstance(o, (pd.Timestamp, datetime)):
            return o.isoformat()
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return str(o)

    return json.dumps(obj, ensure_ascii=False, indent=2, default=default)[:max_chars]


def dataframe_hash(df: pd.DataFrame) -> str:
    preview = df.head(500).to_csv(index=False)
    return hashlib.sha256(preview.encode("utf-8")).hexdigest()[:16]


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def df_to_records_or_dict(result: Any) -> Any:
    if isinstance(result, pd.DataFrame):
        return result.replace({np.nan: None}).to_dict(orient="records")
    return result
