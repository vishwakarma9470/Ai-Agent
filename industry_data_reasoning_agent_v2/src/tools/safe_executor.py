
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd


class SafePandasExecutor:
    """
    Deterministic executor for whitelisted analysis operations.
    LLM creates a JSON plan; this class executes only safe operations.
    """

    VALID_INTENTS = {"summary", "ranking", "comparison", "trend", "correlation", "anomaly", "regression", "pivot"}
    VALID_AGGS = {"sum", "mean", "median", "min", "max", "count"}

    def __init__(self, df: pd.DataFrame, schema: Dict[str, Any]):
        self.df = df
        self.schema = schema

    def execute(self, plan: Dict[str, Any]) -> Tuple[Any, str]:
        intent = plan.get("intent", "summary")
        df = self._apply_filters(self.df.copy(), plan.get("filters", []))

        if intent in {"ranking", "comparison"}:
            return self._group_aggregate(df, plan)
        if intent == "trend":
            return self._trend(df, plan)
        if intent == "correlation":
            return self._correlation(df)
        if intent == "anomaly":
            return self._anomaly(df, plan)
        if intent == "regression":
            return self._regression(df, plan)
        if intent == "pivot":
            return self._pivot(df, plan)
        return self._summary(df)

    def _apply_filters(self, df: pd.DataFrame, filters: List[Dict[str, Any]]) -> pd.DataFrame:
        for f in filters or []:
            if not isinstance(f, dict):
                continue
            col = f.get("column")
            op = str(f.get("op", "==")).lower()
            val = f.get("value")

            if col not in df.columns:
                continue

            try:
                if op == "==":
                    df = df[df[col].astype(str).str.lower() == str(val).lower()]
                elif op == "!=":
                    df = df[df[col].astype(str).str.lower() != str(val).lower()]
                elif op == ">":
                    df = df[pd.to_numeric(df[col], errors="coerce") > float(val)]
                elif op == ">=":
                    df = df[pd.to_numeric(df[col], errors="coerce") >= float(val)]
                elif op == "<":
                    df = df[pd.to_numeric(df[col], errors="coerce") < float(val)]
                elif op == "<=":
                    df = df[pd.to_numeric(df[col], errors="coerce") <= float(val)]
                elif op == "contains":
                    df = df[df[col].astype(str).str.contains(str(val), case=False, na=False)]
                elif op == "in" and isinstance(val, list):
                    allowed = {str(x).lower() for x in val}
                    df = df[df[col].astype(str).str.lower().isin(allowed)]
            except Exception:
                continue
        return df

    def _summary(self, df: pd.DataFrame) -> Tuple[Dict[str, Any], str]:
        summary = {
            "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
            "numeric_summary": df.describe(include=[np.number]).round(3).replace({np.nan: None}).to_dict(),
            "missing_values": {c: int(df[c].isna().sum()) for c in df.columns},
            "duplicate_rows": int(df.duplicated().sum()),
        }
        return summary, f"Dataset has {df.shape[0]} rows, {df.shape[1]} columns, and {int(df.duplicated().sum())} duplicate rows."

    def _group_aggregate(self, df: pd.DataFrame, plan: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
        metric = plan.get("metric")
        dimensions = plan.get("dimensions") or []
        dim = dimensions[0] if dimensions else None
        agg = plan.get("aggregation", "sum")
        top_n = int(plan.get("top_n", 10))

        if not dim:
            return pd.DataFrame(), "Dimension missing."
        if agg != "count" and not metric:
            return pd.DataFrame(), "Metric missing."

        if agg == "count":
            out = df.groupby(dim, dropna=False).size().reset_index(name="count")
            metric_col = "count"
        else:
            out = getattr(df.groupby(dim, dropna=False)[metric], agg)().reset_index()
            metric_col = metric

        out = out.sort_values(metric_col, ascending=False).head(top_n)
        if out.empty:
            return out, "No matching rows after filters."

        best = out.iloc[0]
        return out, f"Highest {metric_col} is for {dim}='{best[dim]}' with value {round(float(best[metric_col]), 2)}."

    def _trend(self, df: pd.DataFrame, plan: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
        date_col = plan.get("date_col")
        metric = plan.get("metric")
        agg = plan.get("aggregation", "sum")
        grain = plan.get("time_grain", "M")

        if not date_col or not metric:
            return pd.DataFrame(), "Date column or metric missing."

        temp = df[[date_col, metric]].dropna().copy()
        temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
        temp = temp.dropna().sort_values(date_col)
        if temp.empty:
            return pd.DataFrame(), "No valid date/metric rows."

        grain = grain if grain in {"D", "W", "M", "Q", "Y"} else "M"
        temp = temp.set_index(date_col)
        if agg == "count":
            out = temp.resample(grain).size().reset_index(name="count")
            metric_col = "count"
        else:
            out = getattr(temp.resample(grain)[metric], agg)().reset_index()
            metric_col = metric
        out = out.rename(columns={date_col: "period"})

        if len(out) >= 2:
            change = float(out[metric_col].iloc[-1] - out[metric_col].iloc[0])
            direction = "increased" if change > 0 else "decreased" if change < 0 else "stayed flat"
            return out, f"{metric_col} {direction} by {round(change, 2)} from first to last period."
        return out, "Not enough time periods for trend interpretation."

    def _correlation(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
        nums = [c for c in self.schema.get("numeric", []) if c in df.columns]
        if len(nums) < 2:
            return pd.DataFrame(), "At least two numeric columns are required."

        corr = df[nums].corr(numeric_only=True)
        pairs = []
        for i, a in enumerate(nums):
            for b in nums[i + 1:]:
                val = corr.loc[a, b]
                if pd.notna(val):
                    pairs.append({
                        "column_1": a,
                        "column_2": b,
                        "correlation": round(float(val), 4),
                        "abs_correlation": round(abs(float(val)), 4),
                    })
        out = pd.DataFrame(pairs).sort_values("abs_correlation", ascending=False).head(15)
        if out.empty:
            return out, "No correlation pairs found."
        row = out.iloc[0]
        return out, f"Strongest correlation is {row['column_1']} vs {row['column_2']} = {row['correlation']}."

    def _anomaly(self, df: pd.DataFrame, plan: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
        metric = plan.get("metric")
        if not metric:
            return pd.DataFrame(), "Metric missing."

        temp = df.copy()
        std = temp[metric].std()
        if pd.isna(std) or std == 0:
            return pd.DataFrame(), "No variation in metric."

        temp["z_score"] = (temp[metric] - temp[metric].mean()) / std
        out = temp[temp["z_score"].abs() > float(plan.get("z_threshold", 2.0))]
        out = out.sort_values("z_score", key=lambda s: s.abs(), ascending=False).head(30)
        return out, f"{len(out)} possible anomalies found using z-score."

    def _regression(self, df: pd.DataFrame, plan: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
        target = plan.get("metric")
        predictor = plan.get("predictor")
        if not target or not predictor:
            return pd.DataFrame(), "Regression needs target metric and predictor."

        temp = df[[predictor, target]].dropna().copy()
        if len(temp) < 3:
            return pd.DataFrame(), "Regression needs at least 3 valid rows."

        x = temp[predictor].astype(float).values
        y = temp[target].astype(float).values
        slope, intercept = np.polyfit(x, y, 1)
        y_hat = slope * x + intercept
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
        corr = float(np.corrcoef(x, y)[0, 1])

        out = pd.DataFrame([{
            "target": target,
            "predictor": predictor,
            "slope": round(float(slope), 6),
            "intercept": round(float(intercept), 6),
            "r2": round(float(r2), 4),
            "correlation": round(corr, 4),
            "rows_used": int(len(temp)),
        }])
        return out, f"{predictor} explains about {round(r2 * 100, 2)}% variance in {target}."

    def _pivot(self, df: pd.DataFrame, plan: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
        metric = plan.get("metric")
        dimensions = plan.get("dimensions") or []
        agg = plan.get("aggregation", "sum")
        if len(dimensions) < 2 or not metric:
            return pd.DataFrame(), "Pivot requires two dimensions and one metric."

        out = pd.pivot_table(
            df,
            values=metric,
            index=dimensions[0],
            columns=dimensions[1],
            aggfunc=agg,
            fill_value=0,
        ).reset_index()
        return out, f"Pivot created for {metric} by {dimensions[0]} and {dimensions[1]}."
