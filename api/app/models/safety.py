from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Integer, String, DateTime, ForeignKey, Index, Text, Boolean, func, JSON
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class RiskFlag(Base):
    __tablename__ = "risk_flag"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("group.id", ondelete="CASCADE"), nullable=False)
    checkpoint_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("checkpoint.id"), nullable=True)
    rule_id: Mapped[str] = mapped_column(String(16), nullable=False)  # R1..R10
    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # info, watch, urgent
    message_en: Mapped[str] = mapped_column(Text, nullable=False)
    message_hi: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)  # open, acked, resolved
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)

    group: Mapped["Group"] = relationship("Group", back_populates="flags")
    checkpoint: Mapped[Optional["Checkpoint"]] = relationship("Checkpoint")

    __table_args__ = (
        Index("ix_risk_flag_status_severity", "status", "severity"),
        Index(
            "uq_open_risk_flag_group_rule",
            "group_id",
            "rule_id",
            unique=True,
            postgresql_where=(status == "open"),
            sqlite_where=(status == "open")
        ),
    )


class SymptomReport(Base):
    __tablename__ = "symptom_report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("group.id", ondelete="CASCADE"), nullable=False)
    checkpoint_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("checkpoint.id"), nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    red_flags: Mapped[list] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=list, nullable=False)
    advice_level: Mapped[str] = mapped_column(String(16), nullable=False)  # normal, mild, moderate, severe
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Incident(Base):
    __tablename__ = "incident"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("group.id", ondelete="CASCADE"), nullable=False)
    flag_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("risk_flag.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., 'missing', 'medical_ams', 'sos'
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)  # open, assigned, resolved
    assigned_to: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ShareToken(Base):
    __tablename__ = "share_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("group.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # 128-bit random hex
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    group: Mapped["Group"] = relationship("Group")


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)  # console, telegram, sms
    target: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_summary: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ok: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
