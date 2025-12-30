from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ColumnType = Literal["string", "number", "date", "url", "boolean"]


class TableColumn(BaseModel):
    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    type: ColumnType


class ResultOut(BaseModel):
    id: str
    run_id: str
    schema_version: int
    columns: list[TableColumn]
    rows: list[dict]
    summary: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


