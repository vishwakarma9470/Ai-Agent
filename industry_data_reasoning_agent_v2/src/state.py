
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid


@dataclass
class AgentMessage:
    agent: str
    status: str
    detail: str
    artifacts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunState:
    query: str
    dataset_path: str
    run_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    llm_enabled: bool = False
    model: str = ""
    raw_df_shape: Optional[List[int]] = None
    clean_df_shape: Optional[List[int]] = None
    schema: Dict[str, Any] = field(default_factory=dict)
    pii_report: Dict[str, Any] = field(default_factory=dict)
    quality_report: Dict[str, Any] = field(default_factory=dict)
    drift_report: Dict[str, Any] = field(default_factory=dict)
    plan: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    chart_path: Optional[str] = None
    insight: str = ""
    verification: Dict[str, Any] = field(default_factory=dict)
    report_path: Optional[str] = None
    fallback: Optional[Dict[str, Any]] = None
    messages: List[AgentMessage] = field(default_factory=list)

    def add(self, agent: str, status: str, detail: str, **artifacts: Any) -> None:
        self.messages.append(AgentMessage(agent=agent, status=status, detail=detail, artifacts=artifacts))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
