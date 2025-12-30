from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


RunStatus = Literal["queued", "running", "success", "failed"]


class RunOut(BaseModel):
    id: str
    task_id: str
    scheduled_for: datetime
    started_at: datetime | None
    finished_at: datetime | None
    status: RunStatus
    error_message: str | None
    llm_model: str | None
    token_usage: dict | None
    cost_estimate: float | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


