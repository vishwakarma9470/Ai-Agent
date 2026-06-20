
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json


class DataDriftAgent:
    """
    Compares current schema with previous run's schema profile.
    Useful when deploying the agent repeatedly on changing datasets.
    """

    def __init__(self, profile_path: str = "runs/latest_profile.json"):
        self.profile_path = Path(profile_path)

    def run(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        current = {
            "columns": schema.get("columns", []),
            "numeric": schema.get("numeric", []),
            "categorical": schema.get("categorical", []),
            "datetime": schema.get("datetime", []),
        }

        report = {
            "has_previous_profile": self.profile_path.exists(),
            "added_columns": [],
            "removed_columns": [],
            "type_group_changes": [],
            "status": "NO_PREVIOUS_PROFILE",
        }

        if self.profile_path.exists():
            previous = json.loads(self.profile_path.read_text(encoding="utf-8"))
            prev_cols = set(previous.get("columns", []))
            curr_cols = set(current.get("columns", []))
            report["added_columns"] = sorted(curr_cols - prev_cols)
            report["removed_columns"] = sorted(prev_cols - curr_cols)

            for group in ["numeric", "categorical", "datetime"]:
                prev = set(previous.get(group, []))
                curr = set(current.get(group, []))
                changed_in = sorted((prev ^ curr) & curr_cols)
                if changed_in:
                    report["type_group_changes"].append({"group": group, "changed_columns": changed_in})

            report["status"] = "DRIFT_DETECTED" if (
                report["added_columns"] or report["removed_columns"] or report["type_group_changes"]
            ) else "NO_DRIFT"

        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        self.profile_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
        return report
