
from __future__ import annotations

import re
from typing import Any, Dict, Tuple
import pandas as pd


class PrivacyPIIAgent:
    """
    Detects obvious PII risk and creates a safe schema summary for LLM prompts.
    This does not fully anonymize data; it prevents raw PII samples from being sent to the planner.
    """

    EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
    PHONE_RE = re.compile(r"(\+?\d[\d\s\-]{8,}\d)")

    def run(self, df: pd.DataFrame) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        report = {"pii_columns": [], "warnings": []}
        safe_samples = {}

        for col in df.columns:
            series = df[col].dropna().astype(str).head(100)
            joined = " ".join(series.tolist())
            risks = []
            if self.EMAIL_RE.search(joined):
                risks.append("email")
            if self.PHONE_RE.search(joined):
                risks.append("phone")
            if any(k in col for k in ["email", "phone", "mobile", "aadhaar", "pan", "ssn"]):
                risks.append("column_name_risk")

            if risks:
                report["pii_columns"].append({"column": col, "risk": sorted(set(risks))})
                safe_samples[col] = ["<redacted>"]
            else:
                # Limit samples to avoid sending large data to LLM
                safe_samples[col] = [str(v)[:60] for v in df[col].dropna().astype(str).unique()[:5]]

        if report["pii_columns"]:
            report["warnings"].append("Potential PII detected. LLM prompt will use redacted samples for risky columns.")

        return report, safe_samples
