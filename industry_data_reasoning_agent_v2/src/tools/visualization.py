
from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


class VisualizationTool:
    def create(self, result: Any, plan: Dict[str, Any], output_path: str) -> Optional[str]:
        if not isinstance(result, pd.DataFrame) or result.empty:
            return None

        chart = plan.get("chart", "table")
        output_path = str(output_path)

        plt.figure(figsize=(11, 6))

        try:
            if chart == "bar" and plan.get("dimensions"):
                dim = plan["dimensions"][0]
                metric = plan.get("metric") if plan.get("metric") in result.columns else "count"
                plt.bar(result[dim].astype(str), result[metric])
                plt.xlabel(dim)
                plt.ylabel(metric)
                plt.title(f"{metric} by {dim}")
                plt.xticks(rotation=30, ha="right")

            elif chart == "line" and "period" in result.columns:
                metric = plan.get("metric") if plan.get("metric") in result.columns else "count"
                plt.plot(pd.to_datetime(result["period"]), result[metric], marker="o")
                plt.xlabel("period")
                plt.ylabel(metric)
                plt.title(f"{metric} trend")

            else:
                table = result.head(12)
                plt.axis("off")
                plt.table(
                    cellText=table.astype(str).values,
                    colLabels=table.columns,
                    loc="center",
                    cellLoc="center",
                )
                plt.title("Analysis Result")

            plt.tight_layout()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=160)
            plt.close()
            return output_path
        except Exception:
            plt.close()
            return None
