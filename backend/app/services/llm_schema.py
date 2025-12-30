from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TableColumn(BaseModel):
    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    type: Literal["string", "number", "date", "url", "boolean"]


class TableResult(BaseModel):
    columns: list[TableColumn]
    rows: list[dict]
    summary: str | None = None

    @model_validator(mode="after")
    def _normalize_rows(self) -> "TableResult":
        """
        Ensure each row has every declared column key (fill missing as null),
        matching the PRD rule: unknown data -> nulls.
        """
        keys = [c.key for c in self.columns]
        normalized: list[dict] = []
        for row in self.rows:
            out = dict(row or {})
            for k in keys:
                out.setdefault(k, None)
            normalized.append(out)
        self.rows = normalized

        # Reject "empty tables" (all values null/empty across all rows)
        if not self.columns or not self.rows:
            raise ValueError("LLM produced an empty table (no columns or no rows)")
        all_empty = True
        for row in self.rows:
            for k in keys:
                v = row.get(k)
                if v is not None and v != "":
                    all_empty = False
                    break
            if not all_empty:
                break
        if all_empty:
            raise ValueError("LLM produced an empty table (all cells were null/empty)")

        return self


