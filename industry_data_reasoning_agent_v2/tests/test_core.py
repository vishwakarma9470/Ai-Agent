
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.pipeline import IndustryDataReasoningPipeline


def test_pipeline_runs_offline():
    pipeline = IndustryDataReasoningPipeline(runs_dir="runs_test")
    out = pipeline.run("data/sample_sales.csv", "top products by revenue")
    assert out["plan"]["intent"] in {"ranking", "summary", "comparison"}
    assert out["verification"]["status"] in {"PASS", "REVIEW_REQUIRED"}
    assert out["report_path"]
