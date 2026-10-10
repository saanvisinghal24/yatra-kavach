from datetime import date
from typing import Optional, List
from sqlalchemy import (
    Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey,
    Index, UniqueConstraint, func, JSON
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class Yatra(Base):
    __tablename__ = "yatra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_hi: Mapped[str] = mapped_column(String(128), nullable=False)
    district: Mapped[str] = mapped_column(String(64), nullable=False)
    season_start: Mapped[date] = mapped_column(Date, nullable=False)
    season_end: Mapped[date] = mapped_column(Date, nullable=False)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_hi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    routes: Mapped[List["Route"]] = relationship("Route", back_populates="yatra", cascade="all, delete-orphan")


class Route(Base):
    __tablename__ = "route"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    yatra_id: Mapped[int] = mapped_column(Integer, ForeignKey("yatra.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), default="trek", nullable=False)  # 'trek' or 'crowd'
    total_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    base_altitude_m: Mapped[int] = mapped_column(Integer, nullable=False)
    max_altitude_m: Mapped[int] = mapped_column(Integer, nullable=False)
    rules_config: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    yatra: Mapped["Yatra"] = relationship("Yatra", back_populates="routes")
    checkpoints: Mapped[List["Checkpoint"]] = relationship("Checkpoint", back_populates="route", cascade="all, delete-orphan", order_by="Checkpoint.seq")


class Checkpoint(Base):
    __tablename__ = "checkpoint"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(Integer, ForeignKey("route.id", ondelete="CASCADE"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_hi: Mapped[str] = mapped_column(String(128), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    altitude_m: Mapped[int] = mapped_column(Integer, nullable=False)
    dist_from_prev_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    min_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    cutoff_time: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)  # "HH:MM"
    capacity_hint: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    facilities: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict, nullable=False)  # medical, oxygen, water, food, shelter
    has_network: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)  # open, congested, closed
    qr_key_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    route: Mapped["Route"] = relationship("Route", back_populates="checkpoints")

    __table_args__ = (
        UniqueConstraint("route_id", "seq", name="uq_checkpoint_route_seq"),
    )
