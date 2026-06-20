
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.pipeline import IndustryDataReasoningPipeline
from src.utils import safe_json


def main():
    parser = argparse.ArgumentParser(description="Industry Data Reasoning Agent")
    parser.add_argument("--data", default="data/sample_sales.csv", help="CSV/XLSX/JSON/Parquet dataset path")
    parser.add_argument("--query", default=None, help="Natural-language analytics question")
    parser.add_argument("--model", default=None, help="OpenAI model name")
    parser.add_argument("--runs-dir", default="runs", help="Output runs directory")
    args = parser.parse_args()

    query = args.query or input("Question: ").strip() or "top products by revenue"

    pipeline = IndustryDataReasoningPipeline(model=args.model, runs_dir=args.runs_dir)
    output = pipeline.run(args.data, query)

    print("\n=== Industry Data Reasoning Agent ===")
    print(f"Run ID: {output['run_id']}")
    print(f"LLM enabled: {output['llm_enabled']}")
    print(f"Model: {output['model']}")

    print("\n--- Plan ---")
    print(json.dumps(output["plan"], indent=2, ensure_ascii=False))

    print("\n--- Insight ---")
    print(output["insight"])

    print("\n--- Verification ---")
    print(json.dumps(output["verification"], indent=2, ensure_ascii=False))

    print("\n--- Artifacts ---")
    print(f"Report: {output.get('report_path')}")
    print(f"Chart: {output.get('chart_path')}")
    print(f"Audit: {Path(args.runs_dir) / output['run_id'] / 'audit_log.json'}")

    if output.get("fallback"):
        print("\n--- General Problem Solver ---")
        print(safe_json(output["fallback"], 5000))


if __name__ == "__main__":
    main()
