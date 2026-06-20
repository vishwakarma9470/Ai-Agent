from __future__ import annotations

from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse, parse_qs
import sqlite3

import pandas as pd

from src.utils import normalize_col


class DataIngestionAgent:
    """
    Loads CSV/XLSX/JSON/Parquet and SQLite tables.

    SQLite format:
    sqlite:///data/sample_sales.db?table=sales
    """

    SUPPORTED = {".csv", ".xlsx", ".xls", ".json", ".parquet"}

    def run(self, path: str) -> Tuple[pd.DataFrame, str]:
        if path.startswith("sqlite:///"):
            return self._load_sqlite(path)

        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")

        suffix = p.suffix.lower()
        if suffix not in self.SUPPORTED:
            raise ValueError(f"Unsupported file type: {suffix}. Supported: {sorted(self.SUPPORTED)}")

        if suffix == ".csv":
            df = pd.read_csv(p)
        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(p)
        elif suffix == ".json":
            df = pd.read_json(p)
        elif suffix == ".parquet":
            df = pd.read_parquet(p)
        else:
            raise ValueError("Unsupported file type.")

        df.columns = [normalize_col(c) for c in df.columns]
        return df, f"Loaded {p.name} with shape {df.shape}."

    def _load_sqlite(self, uri: str) -> Tuple[pd.DataFrame, str]:
        parsed = urlparse(uri)
        query = parse_qs(parsed.query)
        table = query.get("table", [None])[0]

        # urlparse("sqlite:///data/file.db").path => /data/file.db
        # For relative path, support sqlite:///data/sample.db by stripping first slash if needed.
        db_path = parsed.path
        if db_path.startswith("/") and not Path(db_path).exists():
            db_path = db_path[1:]

        if not table:
            raise ValueError("SQLite URI requires ?table=table_name")

        if not Path(db_path).exists():
            raise FileNotFoundError(f"SQLite database not found: {db_path}")

        with sqlite3.connect(db_path) as con:
            df = pd.read_sql_query(f"SELECT * FROM {table}", con)

        df.columns = [normalize_col(c) for c in df.columns]
        return df, f"Loaded SQLite table '{table}' from {db_path} with shape {df.shape}."
