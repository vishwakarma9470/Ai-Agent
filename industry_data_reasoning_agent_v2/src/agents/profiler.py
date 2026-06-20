
from __future__ import annotations

from typing import Any, Dict, Tuple
import pandas as pd

from src.utils import dataframe_hash


class SchemaProfilerAgent:
    """
    Infers numeric/categorical/datetime columns and creates a compact schema for planning.
    """

    def run(self, df: pd.DataFrame, safe_samples: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df = df.copy()
        numeric, categorical, datetime_cols, boolean_cols = [], [], [], []

        for col in df.columns:
            s = df[col]

            if any(k in col for k in ["date", "time", "month", "year", "created_at", "updated_at"]):
                parsed = pd.to_datetime(s, errors="coerce")
                if parsed.notna().mean() >= 0.6:
                    df[col] = parsed
                    datetime_cols.append(col)
                    continue

            if pd.api.types.is_bool_dtype(s):
                boolean_cols.append(col)
                continue

            if pd.api.types.is_numeric_dtype(s):
                numeric.append(col)
                continue

            cleaned = (
                s.astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.replace("%", "", regex=False)
            )
            converted = pd.to_numeric(cleaned, errors="coerce")
            if converted.notna().mean() >= 0.8:
                df[col] = converted
                numeric.append(col)
            else:
                categorical.append(col)

        schema = {
            "columns": list(df.columns),
            "numeric": numeric,
            "categorical": categorical,
            "datetime": datetime_cols,
            "boolean": boolean_cols,
            "rows": int(df.shape[0]),
            "cols": int(df.shape[1]),
            "data_hash_preview": dataframe_hash(df),
            "missing_values": {c: int(df[c].isna().sum()) for c in df.columns},
            "sample_values": safe_samples,
        }
        return df, schema
