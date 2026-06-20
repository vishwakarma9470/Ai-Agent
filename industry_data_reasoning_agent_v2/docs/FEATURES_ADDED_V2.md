# V2 Industry Additions

## 1. FastAPI Backend
Added `api.py`.

Use:
```bash
uvicorn api:app --reload
```

Benefits:
- Other apps can call the agent through REST API.
- This makes the project closer to deployable production architecture.

## 2. API Key RBAC
Added:
- `ADMIN_API_KEY`
- `ANALYST_API_KEY`
- `VIEWER_API_KEY`

Benefits:
- Admin can approve/reject results.
- Analyst can run jobs.
- Viewer can only read results.

## 3. Background Jobs
Endpoint:
```text
POST /jobs
GET /jobs/{job_id}
```

Benefits:
- Long-running analysis does not block the client.
- UI or frontend can poll job status.

## 4. Run Registry with SQLite
Added `RunRegistry` in `src/src/storage.py`.

Benefits:
- Every run/job is tracked in `runs/registry.db`.
- You can list previous runs and fetch reports later.

## 5. Human Approval Workflow
Endpoints:
```text
POST /runs/{run_id}/approve
POST /runs/{run_id}/reject
```

Benefits:
- Low-confidence or warning-heavy results can be reviewed before business use.
- This is important for enterprise decision-support systems.

## 6. SQLite Connector
Data path now supports:
```text
sqlite:///data/sample_sales.db?table=sales
```

Benefits:
- Agent can analyze database tables, not only files.
- This is closer to real business workflows.

## 7. Observability Logs
Added app/API logs in:
```text
runs/app.log
runs/api.log
```

Benefits:
- Debugging and monitoring become easier.
- Production systems need operational visibility.

## 8. PII Masking in Result Artifacts
If obvious PII columns are detected, result artifacts mask those columns.

Benefits:
- Reduces risk of leaking sensitive values in audit/report outputs.

## 9. HTML Report
In addition to `report.md`, V2 generates:
```text
report.html
```

Benefits:
- Report can be opened directly in a browser or shared with non-technical users.

## 10. Docker + API Deployment Direction
Dockerfile remains included and requirements now support API deployment.

Benefits:
- Easier hosting on cloud/VPS/internal server.
