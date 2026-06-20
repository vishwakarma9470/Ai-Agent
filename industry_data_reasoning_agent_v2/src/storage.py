from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.utils import safe_json


class RunRegistry:
    """
    SQLite registry for run/job metadata.
    This gives the project a production-like tracking layer instead of only loose files.
    """

    def __init__(self, db_path: str = "runs/registry.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init(self) -> None:
        with self._connect() as con:
            con.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                job_id TEXT,
                status TEXT NOT NULL,
                query TEXT,
                dataset_path TEXT,
                approval_status TEXT DEFAULT 'not_required',
                approval_note TEXT,
                output_json TEXT,
                report_path TEXT,
                chart_path TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """)
            con.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                run_id TEXT,
                error TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """)

    def create_job(self, job_id: str) -> None:
        now = datetime.utcnow().isoformat() + "Z"
        with self._connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO jobs(job_id,status,created_at,updated_at) VALUES(?,?,?,?)",
                (job_id, "queued", now, now),
            )

    def update_job(self, job_id: str, status: str, run_id: Optional[str] = None, error: Optional[str] = None) -> None:
        now = datetime.utcnow().isoformat() + "Z"
        with self._connect() as con:
            con.execute(
                "UPDATE jobs SET status=?, run_id=COALESCE(?, run_id), error=?, updated_at=? WHERE job_id=?",
                (status, run_id, error, now, job_id),
            )

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as con:
            cur = con.execute("SELECT job_id,status,run_id,error,created_at,updated_at FROM jobs WHERE job_id=?", (job_id,))
            row = cur.fetchone()
        if not row:
            return None
        return dict(zip(["job_id", "status", "run_id", "error", "created_at", "updated_at"], row))

    def save_run(self, output: Dict[str, Any], job_id: Optional[str] = None) -> None:
        run_id = output["run_id"]
        now = datetime.utcnow().isoformat() + "Z"
        verification = output.get("verification", {})
        approval_status = "required" if verification.get("status") != "PASS" else "not_required"

        with self._connect() as con:
            con.execute("""
            INSERT OR REPLACE INTO runs(
                run_id, job_id, status, query, dataset_path, approval_status, approval_note,
                output_json, report_path, chart_path, created_at, updated_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,COALESCE((SELECT created_at FROM runs WHERE run_id=?), ?),?)
            """, (
                run_id,
                job_id,
                "completed",
                output.get("query"),
                output.get("dataset_path"),
                approval_status,
                None,
                safe_json(output, 150000),
                output.get("report_path"),
                output.get("chart_path"),
                run_id,
                now,
                now,
            ))

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as con:
            cur = con.execute("""
            SELECT run_id, job_id, status, query, dataset_path, approval_status, approval_note,
                   output_json, report_path, chart_path, created_at, updated_at
            FROM runs WHERE run_id=?
            """, (run_id,))
            row = cur.fetchone()
        if not row:
            return None

        keys = [
            "run_id", "job_id", "status", "query", "dataset_path", "approval_status", "approval_note",
            "output_json", "report_path", "chart_path", "created_at", "updated_at"
        ]
        data = dict(zip(keys, row))
        try:
            data["output"] = json.loads(data.pop("output_json") or "{}")
        except Exception:
            data["output"] = {}
        return data

    def list_runs(self, limit: int = 25) -> List[Dict[str, Any]]:
        with self._connect() as con:
            cur = con.execute("""
            SELECT run_id, job_id, status, query, approval_status, report_path, chart_path, created_at, updated_at
            FROM runs
            ORDER BY created_at DESC
            LIMIT ?
            """, (limit,))
            rows = cur.fetchall()

        keys = ["run_id", "job_id", "status", "query", "approval_status", "report_path", "chart_path", "created_at", "updated_at"]
        return [dict(zip(keys, row)) for row in rows]

    def approve_run(self, run_id: str, status: str, note: str = "") -> bool:
        now = datetime.utcnow().isoformat() + "Z"
        with self._connect() as con:
            cur = con.execute(
                "UPDATE runs SET approval_status=?, approval_note=?, updated_at=? WHERE run_id=?",
                (status, note, now, run_id),
            )
            return cur.rowcount > 0
