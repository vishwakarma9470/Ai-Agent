
from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd

from src.llm_client import LLMClient
from src.utils import safe_json


class VerificationValidationAgent:
    """
    Validates plan, result, and final insight.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, query: str, schema: Dict[str, Any], plan: Dict[str, Any], result: Any, insight: str, quality_report: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []

        columns = set(schema.get("columns", []))
        numeric = set(schema.get("numeric", []))
        dates = set(schema.get("datetime", []))

        intent = plan.get("intent")
        if intent in {"ranking", "comparison", "trend", "anomaly", "regression", "pivot"}:
            if plan.get("aggregation") != "count" and plan.get("metric") not in numeric:
                issues.append("Metric missing or not numeric.")

        if intent in {"ranking", "comparison"}:
            dims = plan.get("dimensions") or []
            if not dims or dims[0] not in columns:
                issues.append("Dimension missing or invalid.")

        if intent == "trend" and plan.get("date_col") not in dates:
            issues.append("Date column missing or invalid.")

        if intent == "regression":
            if plan.get("predictor") not in numeric:
                issues.append("Predictor missing or invalid.")
            if plan.get("predictor") == plan.get("metric"):
                issues.append("Predictor and target cannot be same.")

        if isinstance(result, pd.DataFrame) and result.empty:
            issues.append("Result is empty.")
        if result is None:
            issues.append("Result is None.")

        if quality_report.get("warnings"):
            issues.append("Data quality warnings exist; interpret results carefully.")

        judge = self._llm_judge(query, plan, result, insight)
        if judge.get("verdict") == "refute":
            issues.append("LLM judge says insight is unsupported by computed result.")
        elif judge.get("verdict") == "partial":
            issues.append("LLM judge says insight is partially supported.")

        confidence = 0.94
        if issues:
            confidence = 0.68
        if "Result is empty." in issues or "Metric missing or not numeric." in issues:
            confidence = 0.45

        return {
            "status": "PASS" if not issues else "REVIEW_REQUIRED",
            "confidence": confidence,
            "issues": issues,
            "llm_judge": judge,
            "checks": [
                "schema-column validation",
                "intent requirement validation",
                "result non-empty validation",
                "data-quality warning review",
                "LLM consistency judge" if self.llm.available else "local judge fallback",
            ],
        }

    def _llm_judge(self, query: str, plan: Dict[str, Any], result: Any, insight: str) -> Dict[str, Any]:
        fallback = {
            "verdict": "support",
            "reason": "LLM not available; rule-based validation completed.",
            "unsupported_claims": [],
        }

        system = """
You are a verification and validation agent.
Judge whether the insight is supported by computed result only.
Return JSON:
{
  "verdict": "support|partial|refute",
  "reason": "...",
  "unsupported_claims": []
}
"""
        result_json = result.head(30).to_dict(orient="records") if isinstance(result, pd.DataFrame) else result
        user = f"""
Query:
{query}

Plan:
{safe_json(plan, 5000)}

Computed result:
{safe_json(result_json, 9000)}

Insight:
{insight}
"""
        return self.llm.json_chat(system, user, fallback)
