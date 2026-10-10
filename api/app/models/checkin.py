from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, ForeignKey,
    Index, func, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class Checkin(Base):
    __tablename__ = "checkin"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # Client-generated UUID
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("group.id", ondelete="CASCADE"), nullable=False)
    checkpoint_id: Mapped[int] = mapped_column(Integer, ForeignKey("checkpoint.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(16), default="self", nullable=False)  # 'self' or 'volunteer'
    volunteer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    headcount: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    client_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    server_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    clock_skew_s: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    invalid_reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    direction: Mapped[str] = mapped_column(String(16), default="outbound", nullable=False)
    member_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    state_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    group: Mapped["Group"] = relationship("Group", back_populates="checkins")
    checkpoint: Mapped["Checkpoint"] = relationship("Checkpoint")

    __table_args__ = (
        Index("ix_checkin_group_client_ts", "group_id", "client_ts"),
        Index("ix_checkin_checkpoint_id", "checkpoint_id"),
    )
