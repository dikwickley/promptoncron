from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Result(Base, TimestampMixin):
    __tablename__ = "results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"), unique=True, index=True)

    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    columns: Mapped[list[dict]] = mapped_column(SQLiteJSON, nullable=False)
    rows: Mapped[list[dict]] = mapped_column(SQLiteJSON, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped["Run"] = relationship(back_populates="result")  # type: ignore[name-defined]


