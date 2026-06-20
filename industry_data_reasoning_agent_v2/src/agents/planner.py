
from __future__ import annotations

from typing import Any, Dict, List
from src.llm_client import LLMClient
from src.utils import normalize_col, safe_json


class QueryPlannerAgent:
    """
    LLM-first planner. It returns a strict JSON plan.
    Fallback planner handles common analysis questions when API key is absent.
    """

    VALID_INTENTS = {"summary", "ranking", "comparison", "trend", "correlation", "anomaly", "regression", "pivot"}
    VALID_AGGS = {"sum", "mean", "median", "min", "max", "count"}

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, query: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        fallback = self._fallback_plan(query, schema)

        system = """
You are a senior analytics planning agent.
Convert the user's natural-language question into a strict JSON analysis plan.

Return JSON only:
{
  "plan": {
    "intent": "summary|ranking|comparison|trend|correlation|anomaly|regression|pivot",
    "metric": "column_or_null",
    "dimensions": ["column"],
    "date_col": "column_or_null",
    "time_grain": "D|W|M|Q|Y",
    "aggregation": "sum|mean|median|min|max|count",
    "filters": [{"column":"...", "op":"==|!=|>|>=|<|<=|contains|in", "value":"..."}],
    "top_n": 10,
    "chart": "bar|line|table",
    "predictor": "column_or_null",
    "z_threshold": 2.0,
    "reason": "why this plan fits",
    "confidence": 0.0
  }
}

Hard rules:
- Use only columns from schema.
- Do not invent data.
- If question asks "impact", "influence", or "predict", use regression if two numeric columns exist.
- If user asks "over time", use trend.
- If user asks "top/highest/best", use ranking.
- If user asks "by/across/compare", use comparison.
- If unsure, use summary with confidence below 0.7.
"""
        user = f"Question:\n{query}\n\nSchema:\n{safe_json(schema, max_chars=11000)}"

        raw = self.llm.json_chat(system, user, {"plan": fallback})
        plan = raw.get("plan", raw)
        return self._sanitize(plan, fallback, schema)

    def _sanitize(self, plan: Dict[str, Any], fallback: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(plan, dict):
            plan = fallback

        columns = set(schema.get("columns", []))
        numeric = set(schema.get("numeric", []))
        datetime_cols = set(schema.get("datetime", []))

        intent = str(plan.get("intent", fallback["intent"])).lower()
        if intent not in self.VALID_INTENTS:
            intent = fallback["intent"]

        def clean_col(x):
            if not x:
                return None
            x = normalize_col(str(x))
            return x if x in columns else None

        metric = clean_col(plan.get("metric")) or fallback.get("metric")
        if metric and metric not in numeric:
            metric = fallback.get("metric") if fallback.get("metric") in numeric else None

        dims = plan.get("dimensions") or fallback.get("dimensions", [])
        if isinstance(dims, str):
            dims = [dims]
        dims = [normalize_col(d) for d in dims if normalize_col(d) in columns]
        if not dims:
            dims = fallback.get("dimensions", [])

        date_col = clean_col(plan.get("date_col")) or fallback.get("date_col")
        if date_col and date_col not in datetime_cols:
            date_col = fallback.get("date_col") if fallback.get("date_col") in datetime_cols else None

        predictor = clean_col(plan.get("predictor")) or fallback.get("predictor")
        if predictor and predictor not in numeric:
            predictor = fallback.get("predictor") if fallback.get("predictor") in numeric else None

        agg = str(plan.get("aggregation", fallback.get("aggregation", "sum"))).lower()
        if agg not in self.VALID_AGGS:
            agg = "sum"

        chart = str(plan.get("chart", fallback.get("chart", "table"))).lower()
        if chart not in {"bar", "line", "table"}:
            chart = fallback.get("chart", "table")

        filters = plan.get("filters", fallback.get("filters", []))
        if not isinstance(filters, list):
            filters = []
        clean_filters = []
        for f in filters:
            if not isinstance(f, dict):
                continue
            col = clean_col(f.get("column"))
            op = str(f.get("op", "==")).lower()
            if col and op in {"==", "!=", ">", ">=", "<", "<=", "contains", "in"}:
                clean_filters.append({"column": col, "op": op, "value": f.get("value")})

        try:
            top_n = max(1, min(100, int(plan.get("top_n", fallback.get("top_n", 10)))))
        except Exception:
            top_n = fallback.get("top_n", 10)

        try:
            confidence = max(0.0, min(1.0, float(plan.get("confidence", fallback.get("confidence", 0.6)))))
        except Exception:
            confidence = fallback.get("confidence", 0.6)

        try:
            z_threshold = float(plan.get("z_threshold", fallback.get("z_threshold", 2.0)))
        except Exception:
            z_threshold = 2.0

        return {
            "intent": intent,
            "metric": metric,
            "dimensions": dims,
            "date_col": date_col,
            "time_grain": str(plan.get("time_grain", fallback.get("time_grain", "M"))).upper(),
            "aggregation": agg,
            "filters": clean_filters,
            "top_n": top_n,
            "chart": chart,
            "predictor": predictor,
            "z_threshold": z_threshold,
            "reason": str(plan.get("reason", fallback.get("reason", ""))),
            "confidence": confidence,
        }

    def _fallback_plan(self, query: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        q = query.lower()
        nums = schema.get("numeric", [])
        cats = schema.get("categorical", [])
        dates = schema.get("datetime", [])

        def pick_metric():
            for word in ["revenue", "sales", "profit", "amount", "quantity", "orders", "price", "cost"]:
                for c in nums:
                    if word in c:
                        return c
            return nums[0] if nums else None

        def pick_dim():
            for word in ["product", "category", "region", "city", "segment", "channel", "customer"]:
                for c in cats:
                    if word in c:
                        return c
            return cats[0] if cats else None

        metric = pick_metric()
        dim = pick_dim()
        date_col = dates[0] if dates else None
        predictor = next((c for c in nums if c != metric), None)

        if any(k in q for k in ["top", "highest", "best", "rank"]):
            intent, chart = "ranking", "bar"
        elif any(k in q for k in ["trend", "over time", "monthly", "daily", "yearly"]):
            intent, chart = "trend", "line"
        elif any(k in q for k in ["compare", "comparison", "by ", "across", "versus", "vs"]):
            intent, chart = "comparison", "bar"
        elif any(k in q for k in ["relationship", "correlation"]):
            intent, chart = "correlation", "table"
        elif any(k in q for k in ["anomaly", "outlier", "unusual", "abnormal"]):
            intent, chart = "anomaly", "table"
        elif any(k in q for k in ["impact", "influence", "predict", "regression"]):
            intent, chart = "regression", "table"
        else:
            intent, chart = "summary", "table"

        return {
            "intent": intent,
            "metric": metric,
            "dimensions": [dim] if dim else [],
            "date_col": date_col,
            "time_grain": "M",
            "aggregation": "sum",
            "filters": [],
            "top_n": 10,
            "chart": chart,
            "predictor": predictor,
            "z_threshold": 2.0,
            "reason": "Fallback local planner selected plan using query keywords and schema.",
            "confidence": 0.62,
        }
