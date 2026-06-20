
from __future__ import annotations

from typing import Any, Dict
import pandas as pd

from src.llm_client import LLMClient
from src.utils import safe_json


class InsightNarrationAgent:
    """
    Turns computed results into concise business-readable insight.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, query: str, plan: Dict[str, Any], result: Any, deterministic_insight: str, quality_report: Dict[str, Any]) -> str:
        fallback = deterministic_insight

        system = """
You are a senior business data analyst.
Write a concise result interpretation.

Rules:
- Use only the computed result and quality report.
- Do not invent numbers.
- Mention limitation if data quality warnings exist.
- Include one decision-oriented recommendation when appropriate.
- Keep it under 140 words.
"""
        result_json = result.head(30).to_dict(orient="records") if isinstance(result, pd.DataFrame) else result
        user = f"""
Question:
{query}

Plan:
{safe_json(plan, 5000)}

Computed result:
{safe_json(result_json, 9000)}

Deterministic insight:
{deterministic_insight}

Data quality:
{safe_json(quality_report, 5000)}
"""
        return self.llm.text_chat(system, user, fallback)
