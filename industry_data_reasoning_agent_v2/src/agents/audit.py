
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json

from src.utils import safe_json


class AuditMemoryAgent:
    """
    Saves audit artifacts and run state.
    """

    def run(self, state_dict: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        p = Path(output_dir)
        p.mkdir(parents=True, exist_ok=True)

        audit_path = p / "audit_log.json"
        audit_path.write_text(safe_json(state_dict, 100000), encoding="utf-8")

        return {"audit_log": str(audit_path)}
