from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import html
import pandas as pd

from src.utils import safe_json


class ReportAgent:
    """
    Generates markdown and HTML reports per run.
    """

    def run(self, state_dict: Dict[str, Any], output_path: str) -> str:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        result = state_dict.get("result")
        if isinstance(result, list):
            result_md = pd.DataFrame(result).head(20).to_markdown(index=False)
        elif isinstance(result, dict):
            result_md = "```json\n" + safe_json(result, 8000) + "\n```"
        else:
            result_md = str(result)

        md = "\n".join([
            "# Data Reasoning Agent Report",
            "",
            f"**Run ID:** `{state_dict.get('run_id')}`",
            f"**Started At:** `{state_dict.get('started_at')}`",
            f"**Query:** {state_dict.get('query')}",
            f"**LLM Enabled:** {state_dict.get('llm_enabled')}",
            f"**Model:** {state_dict.get('model')}",
            "",
            "## Agent Plan",
            "```json",
            safe_json(state_dict.get("plan"), 8000),
            "```",
            "",
            "## Insight",
            state_dict.get("insight", ""),
            "",
            "## Result Preview",
            result_md,
            "",
            "## Verification",
            "```json",
            safe_json(state_dict.get("verification"), 8000),
            "```",
            "",
            "## Data Quality",
            "```json",
            safe_json(state_dict.get("quality_report"), 8000),
            "```",
            "",
            "## PII Report",
            "```json",
            safe_json(state_dict.get("pii_report"), 5000),
            "```",
            "",
            "## Drift Report",
            "```json",
            safe_json(state_dict.get("drift_report"), 5000),
            "```",
        ])

        if state_dict.get("fallback"):
            md += "\n\n## General Problem Solver\n```json\n" + safe_json(state_dict.get("fallback"), 8000) + "\n```"

        p.write_text(md, encoding="utf-8")

        html_path = p.with_suffix(".html")
        html_body = f"""
        <html>
        <head>
          <meta charset="utf-8">
          <title>Data Reasoning Report {html.escape(str(state_dict.get('run_id')))}</title>
          <style>
            body {{ font-family: Arial, sans-serif; margin: 36px; line-height: 1.5; }}
            pre {{ background: #f4f4f4; padding: 14px; overflow-x: auto; }}
            .ok {{ color: #087f23; font-weight: bold; }}
            .warn {{ color: #b26a00; font-weight: bold; }}
          </style>
        </head>
        <body>
          <h1>Data Reasoning Agent Report</h1>
          <p><b>Run ID:</b> {html.escape(str(state_dict.get('run_id')))}</p>
          <p><b>Query:</b> {html.escape(str(state_dict.get('query')))}</p>
          <h2>Insight</h2>
          <p>{html.escape(str(state_dict.get('insight', '')))}</p>
          <h2>Plan</h2><pre>{html.escape(safe_json(state_dict.get('plan'), 8000))}</pre>
          <h2>Verification</h2><pre>{html.escape(safe_json(state_dict.get('verification'), 8000))}</pre>
          <h2>Data Quality</h2><pre>{html.escape(safe_json(state_dict.get('quality_report'), 8000))}</pre>
          <h2>PII Report</h2><pre>{html.escape(safe_json(state_dict.get('pii_report'), 5000))}</pre>
          <h2>Result</h2><pre>{html.escape(safe_json(state_dict.get('result'), 10000))}</pre>
        </body>
        </html>
        """
        html_path.write_text(html_body, encoding="utf-8")
        return str(p)
