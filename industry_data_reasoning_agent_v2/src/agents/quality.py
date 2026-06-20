
from __future__ import annotations

from typing import Any, Dict
import pandas as pd


class DataQualityAgent:
    """
    Produces quality checks useful before analytical reasoning.
    """

    def run(self, df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        report = {
            "row_count": int(df.shape[0]),
            "column_count": int(df.shape[1]),
            "duplicate_rows": int(df.duplicated().sum()),
            "missing_by_column": {c: int(df[c].isna().sum()) for c in df.columns},
            "missing_percentage_by_column": {
                c: round(float(df[c].isna().mean() * 100), 2) for c in df.columns
            },
            "high_missing_columns": [],
            "constant_columns": [],
            "outlier_summary": {},
            "warnings": [],
        }

        for c in df.columns:
            if df[c].isna().mean() > 0.3:
                report["high_missing_columns"].append(c)
            if df[c].nunique(dropna=True) <= 1:
                report["constant_columns"].append(c)

        for c in schema.get("numeric", []):
            std = df[c].std()
            if pd.notna(std) and std != 0:
                z = (df[c] - df[c].mean()) / std
                outliers = int((z.abs() > 3).sum())
                report["outlier_summary"][c] = outliers

        if report["duplicate_rows"]:
            report["warnings"].append("Duplicate rows detected.")
        if report["high_missing_columns"]:
            report["warnings"].append("Some columns have more than 30% missing values.")
        if report["constant_columns"]:
            report["warnings"].append("Some columns are constant and may not be useful for analysis.")

        return report
