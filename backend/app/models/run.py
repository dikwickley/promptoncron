from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Run(Base, TimestampMixin):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), index=True)

    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")  # queued|running|success|failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    llm_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    token_usage: Mapped[dict | None] = mapped_column(SQLiteJSON, nullable=True)
    cost_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)

    task: Mapped["Task"] = relationship(back_populates="runs")  # type: ignore[name-defined]
    result: Mapped["Result | None"] = relationship(back_populates="run", cascade="all,delete", uselist=False)  # type: ignore[name-defined]
    web_search_snapshot: Mapped["WebSearchSnapshot | None"] = relationship(  # type: ignore[name-defined]
        back_populates="run",
        cascade="all,delete",
        uselist=False,
    )


