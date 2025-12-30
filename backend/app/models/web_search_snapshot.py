from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class WebSearchSnapshot(Base, TimestampMixin):
    __tablename__ = "web_search_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"), unique=True, index=True)

    query: Mapped[str] = mapped_column(String(500), nullable=False)
    results: Mapped[list[dict]] = mapped_column(SQLiteJSON, nullable=False)

    run: Mapped["Run"] = relationship(back_populates="web_search_snapshot")  # type: ignore[name-defined]


