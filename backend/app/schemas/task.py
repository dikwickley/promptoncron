from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TaskStatus = Literal["enabled", "disabled"]


class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1)
    cron_expression: str = Field(min_length=1, max_length=120)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    web_search_enabled: bool = False
    status: TaskStatus = "enabled"


class TaskUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    prompt: str | None = Field(default=None, min_length=1)
    cron_expression: str | None = Field(default=None, min_length=1, max_length=120)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    web_search_enabled: bool | None = None
    status: TaskStatus | None = None


class TaskOut(BaseModel):
    id: str
    name: str
    prompt: str
    cron_expression: str
    timezone: str
    web_search_enabled: bool
    status: TaskStatus
    next_run_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


