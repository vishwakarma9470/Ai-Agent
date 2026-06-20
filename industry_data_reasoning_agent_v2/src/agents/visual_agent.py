
from __future__ import annotations

from typing import Any, Dict, Optional
from src.tools.visualization import VisualizationTool


class VisualizationAgent:
    """
    Creates visual artifact from the computed result.
    """

    def run(self, result: Any, plan: Dict[str, Any], output_path: str) -> Optional[str]:
        return VisualizationTool().create(result, plan, output_path)
