
from __future__ import annotations

from typing import Any, Dict, Tuple
import pandas as pd

from src.tools.safe_executor import SafePandasExecutor


class AnalysisExecutionAgent:
    """
    Executes the approved plan using whitelisted Pandas routines.
    """

    def run(self, df: pd.DataFrame, schema: Dict[str, Any], plan: Dict[str, Any]) -> Tuple[Any, str]:
        executor = SafePandasExecutor(df, schema)
        return executor.execute(plan)
