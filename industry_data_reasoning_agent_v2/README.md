# Industry Data Reasoning Agent

This is an upgraded industry-style version of the Data Analysis and Reasoning Agent.

It uses a multi-agent pipeline:

1. DataIngestionAgent
2. PrivacyPIIAgent
3. SchemaProfilerAgent
4. DataQualityAgent
5. DataDriftAgent
6. QueryPlannerAgent
7. AnalysisExecutionAgent
8. VisualizationAgent
9. InsightNarrationAgent
10. VerificationValidationAgent
11. GeneralProblemSolverAgent
12. ReportAgent
13. AuditMemoryAgent

The LLM creates a structured plan, but the project does **not** execute arbitrary LLM-generated Python code. Computation is done through a deterministic safe Pandas executor.

---

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Mac/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set Python path:

Windows PowerShell:

```powershell
$env:PYTHONPATH="src"
```

Mac/Linux:

```bash
export PYTHONPATH=src
```

---

## API key

Copy `.env.example` to `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

Without API key, the project still runs with local fallback planning.

---

## CLI Run

```bash
python cli.py --data data/sample_sales.csv --query "top products by revenue"
```

More examples:

```bash
python cli.py --data data/sample_sales.csv --query "monthly revenue trend"
python cli.py --data data/sample_sales.csv --query "compare profit by region"
python cli.py --data data/sample_sales.csv --query "find anomalies in revenue"
python cli.py --data data/sample_sales.csv --query "relationship between marketing_spend and revenue"
python cli.py --data data/sample_sales.csv --query "does marketing_spend influence revenue"
```

---

## Streamlit UI

```bash
streamlit run app_streamlit.py
```

---

## Outputs

Each run creates a folder:

```text
runs/<run_id>/
  audit_log.json
  chart.png
  report.md
```

---

## Architecture

```text
Dataset + Query
   ↓
DataIngestionAgent
   ↓
PrivacyPIIAgent
   ↓
SchemaProfilerAgent
   ↓
DataQualityAgent
   ↓
DataDriftAgent
   ↓
QueryPlannerAgent
   ↓
AnalysisExecutionAgent
   ↓
VisualizationAgent
   ↓
InsightNarrationAgent
   ↓
VerificationValidationAgent
   ↓
GeneralProblemSolverAgent if confidence is low
   ↓
ReportAgent
   ↓
AuditMemoryAgent
```

---

## Production notes

This is a strong portfolio/industry-style prototype, not a complete enterprise deployment. For actual enterprise use, add:
- authentication and RBAC
- database connectors with secrets manager
- job queue
- observability dashboard
- Docker/Kubernetes deployment
- PII masking policy customized to your domain
- human approval workflow for high-risk decisions
---

# V2 API / Enterprise Features

## FastAPI Backend

Run:

```bash
set PYTHONPATH=src
uvicorn api:app --reload
```

PowerShell:

```powershell
$env:PYTHONPATH="src"
uvicorn api:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Synchronous run:

```bash
curl -X POST "http://127.0.0.1:8000/runs" ^
  -H "X-API-Key: analyst-dev-key" ^
  -H "Content-Type: application/json" ^
  -d "{\"data_path\":\"data/sample_sales.csv\",\"query\":\"top products by revenue\"}"
```

Background job:

```bash
curl -X POST "http://127.0.0.1:8000/jobs" ^
  -H "X-API-Key: analyst-dev-key" ^
  -H "Content-Type: application/json" ^
  -d "{\"data_path\":\"data/sample_sales.csv\",\"query\":\"monthly revenue trend\"}"
```

List runs:

```bash
curl -H "X-API-Key: viewer-dev-key" http://127.0.0.1:8000/runs
```

Approve run:

```bash
curl -X POST "http://127.0.0.1:8000/runs/<run_id>/approve" ^
  -H "X-API-Key: admin-dev-key" ^
  -H "Content-Type: application/json" ^
  -d "{\"note\":\"Reviewed and approved.\"}"
```

## SQLite Connector

Example:

```bash
python cli.py --data "sqlite:///data/sample_sales.db?table=sales" --query "top products by revenue"
```

## V2 Files

```text
api.py                              FastAPI backend
src/src/security.py      API key RBAC
src/src/storage.py       SQLite run/job registry
src/src/config.py        Environment settings
src/src/observability.py Structured logs
docs/FEATURES_ADDED_V2.md           Full V2 feature explanation
run_api_windows.bat                 Windows API launcher
```
