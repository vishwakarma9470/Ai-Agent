
from __future__ import annotations

from typing import Any, Dict
from src.llm_client import LLMClient
from src.utils import safe_json


class GeneralProblemSolverAgent:
    """
    Activates when validation confidence is low or the question is too broad.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, query: str, schema: Dict[str, Any], plan: Dict[str, Any], verification: Dict[str, Any]) -> Dict[str, Any]:
        fallback = {
            "diagnosis": "The request may be broad or required fields may be missing.",
            "subproblems": [
                "Clarify the target metric.",
                "Clarify grouping dimension or time period.",
                "Check data quality warnings.",
                "Run a narrower query."
            ],
            "recommended_questions": [
                "top products by revenue",
                "monthly revenue trend",
                "compare revenue by region",
                "find anomalies in revenue",
                "relationship between marketing_spend and revenue"
            ],
            "next_action": "Ask one specific metric-based question."
        }

        system = """
You are a General Problem Solver for analytics.
Given the failed/low-confidence analysis, decompose the issue and recommend better next queries.
Return JSON only:
{
  "diagnosis": "...",
  "subproblems": [],
  "recommended_questions": [],
  "next_action": "..."
}
"""
        user = f"""
Original query:
{query}

Schema:
{safe_json(schema, 9000)}

Plan:
{safe_json(plan, 5000)}

Verification:
{safe_json(verification, 5000)}
"""
        return self.llm.json_chat(system, user, fallback)
