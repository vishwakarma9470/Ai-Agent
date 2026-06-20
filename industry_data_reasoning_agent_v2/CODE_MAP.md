# Industry Data Reasoning Agent V2

Agar `src/src/__init__.py` almost empty dikhe to ye normal hai. 
Python packages me `__init__.py` sirf package marker hota hai. Real code modules me hota hai.

## Main files

- `cli.py`  
  Terminal se project run karta hai.

- `api.py`  
  FastAPI backend expose karta hai: `/runs`, `/jobs`, `/runs/{run_id}`, approval endpoints.

- `app_streamlit.py`  
  Web UI ke liye Streamlit app.

## Main package

- `src/src/pipeline.py`  
  Sabhi agents ko sequence me run karta hai. Ye project ka orchestrator hai.

- `src/src/state.py`  
  RunState aur AgentMessage dataclasses define karta hai.

- `src/src/llm_client.py`  
  OpenAI API wrapper + fallback logic.

- `src/src/utils.py`  
  Common helpers: JSON conversion, dataframe hash, etc.

- `src/src/config.py`  
  Environment settings: API keys, runs directory, model name.

- `src/src/security.py`  
  Admin/Analyst/Viewer API key RBAC.

- `src/src/storage.py`  
  SQLite registry for runs and background jobs.

- `src/src/observability.py`  
  Logging setup.

## Agents folder

- `src/src/agents/ingestion.py`  
  CSV/Excel/JSON/Parquet/SQLite data load karta hai.

- `src/src/agents/privacy.py`  
  PII detection and redaction.

- `src/src/agents/profiler.py`  
  Schema profiling: numeric, categorical, datetime columns.

- `src/src/agents/quality.py`  
  Missing values, duplicates, outliers, constant columns.

- `src/src/agents/drift.py`  
  Previous schema se current schema compare karta hai.

- `src/src/agents/planner.py`  
  GPT/fallback se JSON analysis plan banata hai.

- `src/src/agents/analysis.py`  
  SafePandasExecutor ko call karta hai.

- `src/src/agents/visual_agent.py`  
  Chart generation tool ko call karta hai.

- `src/src/agents/insight.py`  
  Result ko business-readable insight me convert karta hai.

- `src/src/agents/verification.py`  
  Plan/result/insight validate karta hai.

- `src/src/agents/problem_solver.py`  
  Low-confidence cases me fallback reasoning.

- `src/src/agents/report.py`  
  Markdown + HTML report generate karta hai.

- `src/src/agents/audit.py`  
  audit_log.json save karta hai.

## Tools folder

- `src/src/tools/safe_executor.py`  
  Safe deterministic Pandas operations: ranking, comparison, trend, correlation, anomaly, regression, pivot.

- `src/src/tools/visualization.py`  
  Matplotlib chart generation.

## understood the file 

1. `src/src/pipeline.py`
2. `src/src/agents/planner.py`
3. `src/src/tools/safe_executor.py`
4. `src/src/agents/verification.py`
5. `api.py`
