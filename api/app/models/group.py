from datetime import datetime
from typing import Optional, List
from sqlalchemy import Boolean, Integer, String, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class Group(Base):
    __tablename__ = "group"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(6), unique=True, index=True, nullable=False)
    yatra_id: Mapped[int] = mapped_column(Integer, ForeignKey("yatra.id"), nullable=False)
    route_id: Mapped[int] = mapped_column(Integer, ForeignKey("route.id"), nullable=False)
    leader_name: Mapped[str] = mapped_column(String(128), nullable=False)
    leader_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    emergency_name: Mapped[str] = mapped_column(String(128), nullable=False)
    emergency_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    planned_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_return: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="planned", nullable=False)  # planned/active/completed/flagged/rescued
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    consent_version: Mapped[str] = mapped_column(String(16), default="demo-v1", nullable=False)
    simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    members: Mapped[List["Member"]] = relationship("Member", back_populates="group", cascade="all, delete-orphan")
    checkins: Mapped[List["Checkin"]] = relationship("Checkin", back_populates="group", cascade="all, delete-orphan")
    flags: Mapped[List["RiskFlag"]] = relationship("RiskFlag", back_populates="group", cascade="all, delete-orphan")


class Member(Base):
    __tablename__ = "member"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("group.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    age_band: Mapped[str] = mapped_column(String(16), nullable=False)  # '<18', '18-40', '41-60', '60+'
    note: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    journey_state: Mapped[str] = mapped_column(String(24), default="planned", nullable=False)
    last_visit_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checkpoint_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confirmation_source: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    group: Mapped["Group"] = relationship("Group", back_populates="members")
