from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from src.llm_client import LLMClient
from src.state import RunState
from src.utils import df_to_records_or_dict, ensure_dir
from src.observability import configure_logging, get_logger

from src.agents.ingestion import DataIngestionAgent
from src.agents.privacy import PrivacyPIIAgent
from src.agents.profiler import SchemaProfilerAgent
from src.agents.quality import DataQualityAgent
from src.agents.drift import DataDriftAgent
from src.agents.planner import QueryPlannerAgent
from src.agents.analysis import AnalysisExecutionAgent
from src.agents.visual_agent import VisualizationAgent
from src.agents.insight import InsightNarrationAgent
from src.agents.verification import VerificationValidationAgent
from src.agents.problem_solver import GeneralProblemSolverAgent
from src.agents.report import ReportAgent
from src.agents.audit import AuditMemoryAgent


class IndustryDataReasoningPipeline:
    """
    Industry-style multi-agent analytics pipeline.
    """

    def __init__(self, model: Optional[str] = None, runs_dir: str = "runs"):
        self.runs_dir = runs_dir
        configure_logging(str(Path(runs_dir) / "app.log"))
        self.logger = get_logger("src.pipeline")
        self.llm = LLMClient(model=model)

        self.ingestion = DataIngestionAgent()
        self.privacy = PrivacyPIIAgent()
        self.profiler = SchemaProfilerAgent()
        self.quality = DataQualityAgent()
        self.drift = DataDriftAgent(profile_path=str(Path(runs_dir) / "latest_profile.json"))
        self.planner = QueryPlannerAgent(self.llm)
        self.executor = AnalysisExecutionAgent()
        self.visual = VisualizationAgent()
        self.insight = InsightNarrationAgent(self.llm)
        self.verifier = VerificationValidationAgent(self.llm)
        self.problem_solver = GeneralProblemSolverAgent(self.llm)
        self.reporter = ReportAgent()
        self.audit = AuditMemoryAgent()

    def _mask_pii_columns_in_result(self, result: Any, pii_report: Dict[str, Any]) -> Any:
        """
        Prevent obvious PII columns from appearing in result artifacts.
        This is a prototype-level mask; production should use formal data classification.
        """
        import pandas as pd

        pii_cols = {item.get("column") for item in pii_report.get("pii_columns", []) if item.get("column")}
        if not pii_cols:
            return result

        if isinstance(result, pd.DataFrame):
            result = result.copy()
            for col in pii_cols:
                if col in result.columns:
                    result[col] = "<redacted>"
        return result

    def run(self, dataset_path: str, query: str) -> Dict[str, Any]:
        state = RunState(query=query, dataset_path=dataset_path)
        state.llm_enabled = self.llm.available
        state.model = self.llm.model

        run_dir = ensure_dir(Path(self.runs_dir) / state.run_id)

        # 1. Ingestion
        df_raw, msg = self.ingestion.run(dataset_path)
        state.raw_df_shape = [int(df_raw.shape[0]), int(df_raw.shape[1])]
        state.add("DataIngestionAgent", "OK", msg)

        # 2. Privacy/PII
        pii_report, safe_samples = self.privacy.run(df_raw)
        state.pii_report = pii_report
        state.add("PrivacyPIIAgent", "OK", "PII scan completed.", pii_report=pii_report)

        # 3. Schema profiling
        df, schema = self.profiler.run(df_raw, safe_samples=safe_samples)
        state.schema = schema
        state.clean_df_shape = [int(df.shape[0]), int(df.shape[1])]
        state.add("SchemaProfilerAgent", "OK", "Schema inferred.", schema=schema)

        # 4. Quality
        quality_report = self.quality.run(df, schema)
        state.quality_report = quality_report
        state.add("DataQualityAgent", "OK", "Data quality checks completed.", warnings=quality_report.get("warnings", []))

        # 5. Drift
        drift_report = self.drift.run(schema)
        state.drift_report = drift_report
        state.add("DataDriftAgent", "OK", "Schema drift check completed.", drift_status=drift_report.get("status"))

        # 6. Planning
        plan = self.planner.run(query, schema)
        state.plan = plan
        state.add("QueryPlannerAgent", "OK", "Analysis plan generated.", plan=plan)

        # 7. Analysis execution
        result, deterministic_insight = self.executor.run(df, schema, plan)
        result = self._mask_pii_columns_in_result(result, pii_report)
        state.result = df_to_records_or_dict(result)
        state.add("AnalysisExecutionAgent", "OK", deterministic_insight)

        # 8. Visualization
        chart_path = str(run_dir / "chart.png")
        state.chart_path = self.visual.run(result, plan, chart_path)
        state.add("VisualizationAgent", "OK", "Visualization generated." if state.chart_path else "No visualization generated.", chart_path=state.chart_path)

        # 9. Insight narration
        final_insight = self.insight.run(query, plan, result, deterministic_insight, quality_report)
        state.insight = final_insight
        state.add("InsightNarrationAgent", "OK", "Insight generated.")

        # 10. Verification
        verification = self.verifier.run(query, schema, plan, result, final_insight, quality_report)
        state.verification = verification
        state.add("VerificationValidationAgent", verification.get("status", "OK"), "Validation completed.", verification=verification)

        # 11. General Problem Solver if required
        if verification.get("status") != "PASS" or float(verification.get("confidence", 0)) < 0.75 or float(plan.get("confidence", 0)) < 0.7:
            fallback = self.problem_solver.run(query, schema, plan, verification)
            state.fallback = fallback
            state.add("GeneralProblemSolverAgent", "OK", "Fallback reasoning generated.", fallback=fallback)

        # 12. Report
        state_dict = state.to_dict()
        report_path = self.reporter.run(state_dict, str(run_dir / "report.md"))
        state.report_path = report_path
        state.add("ReportAgent", "OK", "Markdown + HTML report generated.", report_path=report_path)

        # 13. Audit
        final_state = state.to_dict()
        artifacts = self.audit.run(final_state, str(run_dir))
        state.add("AuditMemoryAgent", "OK", "Audit artifacts saved.", **artifacts)

        # Save final audit including AuditMemoryAgent message
        self.audit.run(state.to_dict(), str(run_dir))
        self.logger.info("run_completed run_id=%s verification=%s", state.run_id, state.verification.get("status"))
        return state.to_dict()
